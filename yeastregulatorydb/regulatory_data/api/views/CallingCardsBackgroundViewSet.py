from django.conf import settings
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from yeastregulatorydb.regulatory_data.tasks import promotersetsig_rankedresponse_chained

from ...models import Binding, CallingCardsBackground
from ..filters import CallingCardsBackgroundFilter
from ..serializers import CallingCardsBackgroundSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class CallingCardsBackgroundViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing CallingCardsBackground instances.
    """

    queryset = CallingCardsBackground.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CallingCardsBackgroundSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CallingCardsBackgroundFilter

    def perform_create(self, serializer):
        instance = serializer.save()
        # this attribute is added to the returned serialized data
        # TODO this is copied code btwn this and BindingViewSet
        instance.promotersetsig_processing = False
        lock_id = "add_data_lock"
        acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)
        release_lock = lambda: cache.delete(lock_id)

        if acquire_lock():
            try:
                for binding_obj in Binding.objects.all():
                    # TODO there is repeated code here and in BindingViewSet
                    task_type = None
                    if binding_obj.source.assay == "chipexo":
                        if binding_obj.source.name == "chipexo_pugh_allevents":
                            task_type = settings.CHIPEXO_PROMOTER_SIG_FORMAT
                    elif binding_obj.source.assay == "callingcards":
                        task_type = settings.CALLINGCARDS_PROMOTER_SIG_FORMAT

                    if task_type:
                        instance.promotersetsig_processing = True
                        promotersetsig_rankedresponse_chained(
                            binding_obj.id, self.request.user.id, task_type, background_id=instance.id
                        )
            finally:
                release_lock()
