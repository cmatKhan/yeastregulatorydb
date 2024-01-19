from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from ...models import Binding, PromoterSet
from ...tasks import promotersetsig_rankedresponse_chained
from ..filters.PromoterSetFilter import PromoterSetFilter
from ..serializers.PromoterSetSerializer import PromoterSetSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class PromoterSetViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PromoterSet instances.
    """

    queryset = PromoterSet.objects.select_related("uploader").all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PromoterSetFilter


@transaction.atomic
def perform_create(self, serializer):
    try:
        instance = serializer.save()
    except IntegrityError as e:
        raise ValidationError({"promoterset": str(e)})
    if instance is None:
        raise ValidationError(
            {"promoterset": "Could not save PromoterSet instance. " "Not sure why. Check logs and contact your admin"}
        )

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
                    if self.request.query_params.get("test"):
                        promotersetsig_rankedresponse_chained(
                            binding_obj.id, self.request.user.id, task_type, promoterset_id=instance.id, testing=True
                        )
                    else:
                        transaction.on_commit(
                            lambda: promotersetsig_rankedresponse_chained(
                                binding_obj.id, self.request.user.id, task_type, promoterset_id=instance.id
                            )
                        )
        finally:
            release_lock()
