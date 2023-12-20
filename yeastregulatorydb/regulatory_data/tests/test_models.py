from django.db.models.query import QuerySet
from django.urls import reverse

from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingManualQC,
    CallingCardsBackground,
    ChrMap,
    DataSource,
    Expression,
    ExpressionManualQC,
    FileFormat,
    GenomicFeature,
    PromoterSet,
    PromoterSetSig,
    RankResponse,
    Regulator,
)


def test_binding_get_absolute_url(binding: Binding):
    assert reverse("api:binding-list") == "/api/binding/"
    assert reverse("api:binding-detail", args=[str(binding.id)]) == f"/api/binding/{binding.id}/"


def test_bindingmanualqc_get_absolute_url(bindingmanualqc: BindingManualQC):
    assert reverse("api:bindingmanualqc-list") == "/api/bindingmanualqc/"
    assert (
        reverse("api:bindingmanualqc-detail", args=[str(bindingmanualqc.id)])
        == f"/api/bindingmanualqc/{bindingmanualqc.id}/"
    )


def test_datasource_get_absolute_url(datasource: DataSource):
    assert reverse("api:datasource-list") == "/api/datasource/"
    assert reverse("api:datasource-detail", args=[str(datasource.id)]) == f"/api/datasource/{datasource.id}/"


def test_callingcardsbackground_get_absolute_url(callingcardsbackground: CallingCardsBackground):
    assert reverse("api:callingcardsbackground-list") == "/api/callingcardsbackground/"
    assert (
        reverse("api:callingcardsbackground-detail", args=[str(callingcardsbackground.id)])
        == f"/api/callingcardsbackground/{callingcardsbackground.id}/"
    )


def test_chrmap_get_absolute_url(chrmap: QuerySet):
    assert reverse("api:chrmap-list") == "/api/chrmap/"
    chrmap_instance = ChrMap.objects.first()
    assert reverse("api:chrmap-detail", args=[str(chrmap_instance.id)]) == f"/api/chrmap/{chrmap_instance.id}/"


def test_expression_get_absolute_url(expression: Expression):
    assert reverse("api:expression-list") == "/api/expression/"
    assert reverse("api:expression-detail", args=[str(expression.id)]) == f"/api/expression/{expression.id}/"


def test_expressionmanualqc_get_absolute_url(expressionmanualqc: ExpressionManualQC):
    assert reverse("api:expressionmanualqc-list") == "/api/expressionmanualqc/"
    assert (
        reverse("api:expressionmanualqc-detail", args=[str(expressionmanualqc.id)])
        == f"/api/expressionmanualqc/{expressionmanualqc.id}/"
    )


def test_fileformat_get_absolute_url(fileformat: QuerySet):
    assert reverse("api:fileformat-list") == "/api/fileformat/"
    bed6_id = FileFormat.objects.filter(fileformat="bed6").first().id
    assert reverse("api:fileformat-detail", args=[str(bed6_id)]) == f"/api/fileformat/{bed6_id}/"


def test_genomicfeature_get_absolute_url(genomicfeature: GenomicFeature):
    assert reverse("api:genomicfeature-list") == "/api/genomicfeature/"
    assert (
        reverse("api:genomicfeature-detail", args=[str(genomicfeature.id)])
        == f"/api/genomicfeature/{genomicfeature.id}/"
    )


def test_promoterset_get_absolute_url(promoterset: PromoterSet):
    assert reverse("api:promoterset-list") == "/api/promoterset/"
    assert reverse("api:promoterset-detail", args=[str(promoterset.id)]) == f"/api/promoterset/{promoterset.id}/"


def test_promotersetsig_get_absolute_url(promotersetsig: PromoterSetSig):
    assert reverse("api:promotersetsig-list") == "/api/promotersetsig/"
    assert (
        reverse("api:promotersetsig-detail", args=[str(promotersetsig.id)])
        == f"/api/promotersetsig/{promotersetsig.id}/"
    )


def test_regulator_get_absolute_url(regulator: Regulator):
    assert reverse("api:regulator-list") == "/api/regulator/"
    assert reverse("api:regulator-detail", args=[str(regulator.id)]) == f"/api/regulator/{regulator.id}/"


def test_rank_response_absolute_url(rankresponse: RankResponse):
    assert reverse("api:rankresponse-list") == "/api/rankresponse/"
    assert reverse("api:rankresponse-detail", args=[str(rankresponse.id)]) == f"/api/rankresponse/{rankresponse.id}/"
    assert reverse("api:rankresponse-summary") == "/api/rankresponse/summary/"
