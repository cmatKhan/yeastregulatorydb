from celery import chain
from django.conf import settings

from config import celery_app
from yeastregulatorydb.regulatory_data.models import Binding

from .BaseTask import MyBaseTask
from .combine_cc_passing_replicates_task import combine_cc_passing_replicates_task
from .promoter_significance_task import promoter_significance_task


@celery_app.task()
def promotersetsig_rankedresponse_chained(binding_id, user_id, promotersetsig_filetype, **kwargs):
    """Chain the promoter significance and rank response tasks together

    :param binding_id: The id of the Binding record
    :type binding_id: int
    :param user_id: The id of the user who initiated the task
    :type user_id: int
    :param promotersetsig_filetype: The name of the output FileFormat
    :type promotersetsig_filetype: str
    :param kwargs: Additional keyword arguments. See the additional arguments
    documentation of the :func:`promoter_significance_task` and
    :func:`rank_response_task` functions for more details.

    :return: The result of the task
    :rtype: celery.result.AsyncResult
    """
    # Create a chain of tasks
    task = chain(
        promoter_significance_task.s(binding_id, user_id, promotersetsig_filetype, **kwargs),
    )
    result = task.apply_async()
    return result


@celery_app.task(bind=True, base=MyBaseTask)
def combine_cc_passing_replicates_promotersig_chained(self, user_id, **kwargs):
    """Chain the combine_cc_passing_replicates and promoter_significance tasks together

    :param user_id: The id of the user who initiated the task
    :type user_id: int
    :param kwargs: Additional keyword arguments. See the additional arguments
    documentation of the :func:`combine_cc_passing_replicates_task` and
    :func:`promoter_significance_task` functions for more details.

    :return: The result of the task
    :rtype: celery.result.AsyncResult
    """
    # if regulator_id is in kwargs, then call the task chain using it.
    # otherwise, get a list of all callingcards regulator_ids and
    # call the task chain for each
    regulator_id_list = (
        [kwargs.pop("regulator_id")]
        if kwargs.get("regulator_id")
        else Binding.objects.filter(source__assay="callingcards")
        .exclude(batch="cc_combined")
        .values_list("regulator_id", flat=True)
        .distinct()
    )

    # NOTE: `deduplicate_experiment` is set to False in promoter_significance_task().
    # @hen calculating signficance, we do not want to deduplicate since multiple hops
    # may be recorded at the same coordinate from different experiments. However, note
    # that in combine_cc_passing_replicates_task(), each individual qbed is deduplicated
    # to remove insertions with the same coordinate on opposite strands (so there is
    # just one record in that case).

    task_ids = []
    for regulator_id in regulator_id_list:
        # Create a chain of tasks
        task = chain(
            combine_cc_passing_replicates_task.s(regulator_id, user_id, **kwargs),
            promoter_significance_task.s(
                user_id, settings.CALLINGCARDS_PROMOTER_SIG_FORMAT, deduplicate_experiment=False, **kwargs
            ),
        )
        result = task.apply_async()
        task_ids.append(result.id)
    return task_ids
