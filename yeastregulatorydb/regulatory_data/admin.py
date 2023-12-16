# pylint: disable=unused-import
from django.contrib import admin

# Register your models here.
from .models import (
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
    Regulator,
)

admin.register(Binding)
admin.register(BindingManualQC)
admin.register(DataSource)
admin.register(CallingCardsBackground)
admin.register(ChrMap)
admin.register(Expression)
admin.register(ExpressionManualQC)
admin.register(FileFormat)
admin.register(GenomicFeature)
admin.register(PromoterSet)
admin.register(PromoterSetSig)
admin.register(Regulator)
