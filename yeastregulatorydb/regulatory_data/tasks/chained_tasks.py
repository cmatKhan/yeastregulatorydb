from celery import chain

from config import celery_app

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
