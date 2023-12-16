from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from yeastregulatorydb.regulatory_data.api.views import (
    BindingManualQCViewSet,
    BindingViewSet,
    CallingCardsBackgroundViewSet,
    ChrMapViewSet,
    DataSourceViewSet,
    ExpressionManualQCViewSet,
    ExpressionViewSet,
    FileFormatViewSet,
    GenomicFeatureViewSet,
    PromoterSetSigViewSet,
    PromoterSetViewSet,
    RegulatorViewSet,
)
from yeastregulatorydb.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("bindingmanualqc", BindingManualQCViewSet)
router.register("datasource", DataSourceViewSet)
router.register("binding", BindingViewSet)
router.register("callingcardsbackground", CallingCardsBackgroundViewSet)
router.register("chrmap", ChrMapViewSet)
router.register("expressionmanualqc", ExpressionManualQCViewSet)
router.register("expression", ExpressionViewSet)
router.register("fileformat", FileFormatViewSet)
router.register("genomicfeature", GenomicFeatureViewSet)
router.register("promotersetsig", PromoterSetSigViewSet)
router.register("promoterset", PromoterSetViewSet)
router.register("regulator", RegulatorViewSet)


app_name = "api"
urlpatterns = router.urls
