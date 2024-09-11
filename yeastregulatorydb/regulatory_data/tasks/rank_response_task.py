import logging
import tempfile
from math import ceil as ceiling

import pandas as pd
from callingcardstools.Analysis.yeast import rank_response

from config import celery_app
from yeastregulatorydb.regulatory_data.models import Expression, PromoterSetSig
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


@celery_app.task(serializer="json")
def rank_response_tasks(promotersetsig_ids: list, user_id: int, **kwargs) -> None:
    """
    Iterate over a list of PromoterSetSig object ids and call the
    rank_response_task. The kwargs are passed to the rank_response_task

    :param promotersetsig_ids: A list of promotersetsig object ids
    :type promotersetsig_ids: list
    :param user_id: the id of the user that initiated the task
    :type user_id: int
    :param kwargs: keyword arguments to be passed to the rank_response_task
    """
    for promotersetsig_id in promotersetsig_ids:
        rank_response_task.delay(promotersetsig_id, user_id, **kwargs)


@celery_app.task(serializer="json")
def rank_response_task(
    promotersetsig_id: int,
    **kwargs,
) -> list:
    try:
        promotersetsig_record = PromoterSetSig.objects.get(id=promotersetsig_id)
    except PromoterSetSig.DoesNotExist:
        raise ValueError(f"PromoterSetSig record with id {promotersetsig_id} does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        promotersetsig_filepath = extract_file_from_storage(promotersetsig_record.file, tmpdir)

        # either get the expression object using the expression_id, or get
        # an iterator over all expression objects with the same regulator
        # as the promotersetsig regulator
        expression_objects_iterator = (
            Expression.objects.filter(id=kwargs.get("expression_id")).iterator()
            if "expression_id" in kwargs
            else Expression.objects.filter(regulator=promotersetsig_record.get_genomicfeature()).iterator()
        )

        results_dict = {}
        for record in expression_objects_iterator:
            expression_filepath = extract_file_from_storage(record.file, tmpdir)

            # if the expression pval column is none, set the thres to none. This
            # is in the event that there is no pvalue column
            # TODO consider requiring a pvalue column?
            expression_pval_threshold = (
                None
                if record.source.fileformat.pval_col == "none" or record.source.fileformat.pval_col is None
                else float(
                    kwargs.get("expression_pvalue_threshold", record.source.fileformat.default_pvalue_threshold)
                )
            )

            expression_effect_threshold = float(
                kwargs.get("expression_effect_threshold", record.source.fileformat.default_effect_threshold)
            )

            rank_bin_size = int(kwargs.get("rank_bin_size", 5))

            rank_by_binding_effect = kwargs.get("rank_by_binding_effect", False)
            if isinstance(rank_by_binding_effect, str):
                # verify first that the string is a variant of true or false
                if rank_by_binding_effect.lower() not in ["true", "false"]:
                    raise ValueError(
                        "The value for the 'rank_by_binding_effect' key must be either 'true' or 'false' "
                        "if it is a string"
                    )
                rank_by_binding_effect = rank_by_binding_effect.lower() == "true"

            config_dict = {
                "binding_data_path": [promotersetsig_filepath],
                "binding_source": promotersetsig_record.get_source_name().name,
                "binding_identifier_col": promotersetsig_record.fileformat.feature_identifier_col,
                "binding_effect_col": promotersetsig_record.fileformat.effect_col,
                "binding_pvalue_col": promotersetsig_record.fileformat.pval_col,
                "rank_by_binding_effect": rank_by_binding_effect,
                "expression_data_path": [expression_filepath],
                "expression_source": record.source.name,
                "expression_identifier_col": record.source.fileformat.feature_identifier_col,
                "expression_effect_col": record.source.fileformat.effect_col,
                "expression_effect_thres": expression_effect_threshold,
                "expression_pvalue_col": record.source.fileformat.pval_col,
                "expression_pvalue_thres": expression_pval_threshold,
                "rank_bin_size": rank_bin_size,
                "normalization_threshold": kwargs.get("normalization_threshold", -1),
            }

            # "output_file": kwargs.get("output_file", "rank_response.csv"),
            # "compress": kwargs.get("compress", False),

            # validate the configuration key/value pairs
            args = rank_response.validate_config(config_dict)

            rank_response_df, labeled_binding_response_df, random_expectation_df = (
                rank_response.create_rank_response_table(args)
            )

            # note that the `id` needs to be like this in order for the return to be
            # consistent with the RetrieveRecordsAndFilesMixin
            # if kwargs.get("summary", True) is True, return the rank_response_df
            # summarized by rank_bin. Else, return the labeled_binding_response_df
            results_dict[record.id] = {
                "id": str(promotersetsig_id) + "_" + str(record.id),
                "promotersetsig_id": promotersetsig_id,
                "data": (
                    rank_response_df.to_dict()
                    if kwargs.get("summary", True)
                    else labeled_binding_response_df.to_dict()
                ),
                "n_responsive": int(random_expectation_df.responsive[0]),
                "total_expression_genes": float(
                    random_expectation_df.unresponsive[0] + random_expectation_df.responsive[0]
                ),
            }

    return results_dict
