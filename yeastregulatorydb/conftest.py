import pytest

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
from yeastregulatorydb.regulatory_data.tests.factories import (
    BindingFactory,
    BindingManualQCFactory,
    BindingSourceFactory,
    CallingCardsBackgroundFactory,
    ChrMapFactory,
    ExpressionFactory,
    ExpressionManualQCFactory,
    ExpressionSourceFactory,
    FileFormatFactory,
    GenomicFeatureFactory,
    PromoterSetFactory,
    PromoterSetSigFactory,
    RegulatorFactory,
)
from yeastregulatorydb.users.models import User
from yeastregulatorydb.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def binding(db) -> Binding:
    return BindingFactory()


@pytest.fixture
def bindingmanualqc(db) -> BindingManualQC:
    return BindingManualQCFactory()


@pytest.fixture
def bindingsource(db) -> BindingSource:
    return BindingSourceFactory()


@pytest.fixture
def callingcardsbackground(db) -> CallingCardsBackground:
    return CallingCardsBackgroundFactory()


@pytest.fixture
def chrmap(db) -> ChrMap:
    return ChrMapFactory()


@pytest.fixture
def expression(db) -> Expression:
    return ExpressionFactory()


@pytest.fixture
def expressionmanualqc(db) -> ExpressionManualQC:
    return ExpressionManualQCFactory()


@pytest.fixture
def expressionsource(db) -> ExpressionSource:
    return ExpressionSourceFactory()


@pytest.fixture
def fileformat(db) -> FileFormat:
    return FileFormatFactory()


@pytest.fixture
def genomicfeature(db) -> GenomicFeature:
    return GenomicFeatureFactory()


@pytest.fixture
def promoterset(db) -> PromoterSet:
    return PromoterSetFactory()


@pytest.fixture
def promotersetsig(db) -> PromoterSetSig:
    return PromoterSetSigFactory()


@pytest.fixture
def regulator(db) -> Regulator:
    return RegulatorFactory()
