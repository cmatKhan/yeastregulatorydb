from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from yeastregulatorydb.regulatory_data.tasks import promoter_significance_task

from ...models import Binding, CallingCardsBackground
from ..filters import CallingCardsBackgroundFilter
from ..serializers import CallingCardsBackgroundSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class CallingCardsBackgroundViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing CallingCardsBackground instances.
    """

    queryset = CallingCardsBackground.objects.select_related("uploader", "fileformat").all().order_by("-id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CallingCardsBackgroundSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CallingCardsBackgroundFilter

    def get_serializer_context(self):
        """
        Overriding the get_serializer_context method allows you to add
        extra context for all serializers derived from this viewset.
        """
        context = super().get_serializer_context()
        # Adding custom kwargs to the context. This passes the deduplicate_strands
        # argument to the FileValidationMixin which passes it along to the validate()
        # function. It prevents deduplication of rows based on `chr` `start` `end`.
        # the adh1 and dsir4 background files are combinations of many runs, so
        # duplicates are legitimate hops. Default is to deduplicate, which eliminates
        # locations at the same coordinate on different strand. CC is not stranded,
        # so this is appropriate
        context["deduplicate_strands"] = self.kwargs.get("deduplicate_strands", False)
        return context

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.promotersetsig_processing = False

        lock_id = "add_data_lock"
        acquire_lock = lambda: cache.add(lock_id, "lock", timeout=60 * 60)
        release_lock = lambda: cache.delete(lock_id)

        if acquire_lock():
            try:
                callingcards_bindings = Binding.objects.filter(source__assay="callingcards")
                task_type = settings.CALLINGCARDS_PROMOTER_SIG_FORMAT

                # Check for the "testing" parameter in request data or query parameters
                is_testing = (
                    self.request.data.get("testing", "false").lower() == "true"
                    or self.request.query_params.get("testing", "false").lower() == "true"
                )

                for binding_obj in callingcards_bindings:
                    # Capture the current loop variables for each lambda function
                    if is_testing:
                        promoter_significance_task.delay(
                            binding_obj.id, self.request.user.id, task_type, background_id=instance.id
                        )
                    else:
                        transaction.on_commit(
                            lambda binding_obj_id=binding_obj.id, user_id=self.request.user.id, task_type=task_type, instance_id=instance.id: promoter_significance_task.delay(
                                binding_obj_id, user_id, task_type, background_id=instance_id
                            )
                        )
            finally:
                release_lock()
