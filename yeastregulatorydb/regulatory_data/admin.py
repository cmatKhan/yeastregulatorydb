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
    RankResponse,
    Regulator,
)

admin.site.register(Binding)
admin.site.register(BindingManualQC)
admin.site.register(DataSource)
admin.site.register(CallingCardsBackground)
admin.site.register(ChrMap)
admin.site.register(Expression)
admin.site.register(ExpressionManualQC)
admin.site.register(FileFormat)
admin.site.register(GenomicFeature)
admin.site.register(PromoterSet)
admin.site.register(PromoterSetSig)
admin.site.register(RankResponse)
admin.site.register(Regulator)
