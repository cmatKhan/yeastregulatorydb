from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingManualQC,
    BindingSource,
    CallingCardsBackground,
    ChrMap,
    Expression,
    ExpressionManualQC,
    ExpressionSource,
    FileFormat,
    GenomicFeature,
    PromoterSet,
    PromoterSetSig,
    Regulator,
)


def test_binding_get_absolute_url(binding: Binding):
    assert binding.get_absolute_url() == f"/binding/{binding.id}/"


def test_bindingmanualqc_get_absolute_url(bindingmanualqc: BindingManualQC):
    assert bindingmanualqc.get_absolute_url() == f"/bindingmanualqc/{bindingmanualqc.id}/"


def test_bindingsource_get_absolute_url(bindingsource: BindingSource):
    assert bindingsource.get_absolute_url() == f"/bindingsource/{bindingsource.id}/"


def test_callingcardsbackground_get_absolute_url(callingcardsbackground: CallingCardsBackground):
    assert callingcardsbackground.get_absolute_url() == f"/callingcardsbackground/{callingcardsbackground.id}/"


def test_chrmap_get_absolute_url(chrmap: ChrMap):
    assert chrmap.get_absolute_url() == f"/chrmap/{chrmap.id}/"


def test_expression_get_absolute_url(expression: Expression):
    assert expression.get_absolute_url() == f"/expression/{expression.id}/"


def test_expressionmanualqc_get_absolute_url(expressionmanualqc: ExpressionManualQC):
    assert expressionmanualqc.get_absolute_url() == f"/expressionmanualqc/{expressionmanualqc.id}/"


def test_expressionsource_get_absolute_url(expressionsource: ExpressionSource):
    assert expressionsource.get_absolute_url() == f"/expressionsource/{expressionsource.id}/"


def test_fileformat_get_absolute_url(fileformat: FileFormat):
    assert fileformat.get_absolute_url() == f"/fileformat/{fileformat.id}/"


def test_genomicfeature_get_absolute_url(genomicfeature: GenomicFeature):
    assert genomicfeature.get_absolute_url() == f"/genomicfeature/{genomicfeature.id}/"


def test_promoterset_get_absolute_url(promoterset: PromoterSet):
    assert promoterset.get_absolute_url() == f"/promoterset/{promoterset.id}/"


def test_promotersetsig_get_absolute_url(promotersetsig: PromoterSetSig):
    assert promotersetsig.get_absolute_url() == f"/promotersetsig/{promotersetsig.id}/"


def test_regulator_get_absolute_url(regulator: Regulator):
    assert regulator.get_absolute_url() == f"/regulator/{regulator.id}/"
