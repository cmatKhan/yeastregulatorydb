from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from yeastregulatorydb.regulatory_data.api.views import (
    BindingConcatenatedViewSet,
    BindingManualQCViewSet,
    BindingViewSet,
    CallingCardsBackgroundViewSet,
    ChrMapViewSet,
    DataSourceViewSet,
    DTOViewSet,
    ExpressionManualQCViewSet,
    ExpressionViewSet,
    FileFormatViewSet,
    GenomicFeatureViewSet,
    PromoterSetSigViewSet,
    PromoterSetViewSet,
    RankResponseViewSet,
    RegulatorViewSet,
    UnivariateModelsViewSet,
)
from yeastregulatorydb.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("binding", BindingViewSet)
router.register("bindingconcatenated", BindingConcatenatedViewSet)
router.register("bindingmanualqc", BindingManualQCViewSet)
router.register("callingcardsbackground", CallingCardsBackgroundViewSet)
router.register("chrmap", ChrMapViewSet)
router.register("datasource", DataSourceViewSet)
router.register("dto", DTOViewSet)
router.register("expressionmanualqc", ExpressionManualQCViewSet)
router.register("expression", ExpressionViewSet)
router.register("fileformat", FileFormatViewSet)
router.register("genomicfeature", GenomicFeatureViewSet)
router.register("promotersetsig", PromoterSetSigViewSet)
router.register("promoterset", PromoterSetViewSet)
router.register("rankresponse", RankResponseViewSet)
router.register("regulator", RegulatorViewSet)
router.register("univariatemodels", UnivariateModelsViewSet)


app_name = "api"
urlpatterns = router.urls
