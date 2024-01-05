import pytest

from yeastregulatorydb.regulatory_data.api.filters import (
    BindingFilter,
    BindingManualQCFilter,
    CallingCardsBackgroundFilter,
    DataSourceFilter,
    ExpressionFilter,
    ExpressionManualQCFilter,
    FileFormatFilter,
    GenomicFeatureFilter,
    PromoterSetFilter,
    PromoterSetSigFilter,
    RankResponseFilter,
    RegulatorFilter,
)
from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingManualQC,
    CallingCardsBackground,
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

from .factories import (
    BindingFactory,
    BindingManualQCFactory,
    CallingCardsBackgroundFactory,
    ChrMapFactory,
    DataSourceFactory,
    ExpressionFactory,
    ExpressionManualQCFactory,
    FileFormatFactory,
    GenomicFeatureFactory,
    PromoterSetFactory,
    PromoterSetSigFactory,
    RankResponseFactory,
    RegulatorFactory,
)


@pytest.mark.django_db
def test_binding_filter():
    # Create some bindings using the factory
    regulator1 = RegulatorFactory()
    regulator2 = RegulatorFactory()
    source1 = DataSourceFactory()
    source2 = DataSourceFactory()
    binding1 = BindingFactory(
        regulator=regulator1,
        id=1,
        batch="batch1",
        replicate=1,
        source=source1,
        source_orig_id="1",
        strain="strain1",
        condition="unknown",
    )
    binding2 = BindingFactory(
        regulator=regulator2,
        id=2,
        batch="batch2",
        replicate=2,
        source=source2,
        source_orig_id="2",
        strain="strain2",
        condition="YPD",
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"regulator": regulator1.id},
        {"regulator_locus_tag": regulator1.genomicfeature.locus_tag},
        {"regulator_symbol": regulator1.genomicfeature.symbol},
        {"batch": "batch1"},
        {"replicate": 1},
        {"source": source1.id},
        {"condition": binding1.condition},
        {"source_orig_id": "1"},
        {"strain": "strain1"},
        {"lab": source1.lab},
        {"assay": source1.assay},
        {"workflow": source1.workflow},
    ]

    # Apply each filter and check if it returns the expected bindings
    for params in filter_params:
        f = BindingFilter(params, queryset=Binding.objects.all())
        assert binding1 in f.qs, params
        assert binding2 not in f.qs, params


@pytest.mark.django_db
def test_binding_manual_qc_filter():
    # Create some bindings using the factory
    regulator1 = RegulatorFactory()
    regulator2 = RegulatorFactory()
    datasource1 = DataSourceFactory()
    binding1 = BindingFactory(regulator=regulator1, id=1, batch="batch1", source=datasource1)
    datasource2 = DataSourceFactory()
    binding2 = BindingFactory(regulator=regulator2, id=2, batch="batch2", source=datasource2)
    binding_manual_qc1 = BindingManualQCFactory(
        binding=binding1,
        id=1,
        best_datatype=True,
        data_usable=True,
        passing_replicate=True,
    )
    binding_manual_qc2 = BindingManualQCFactory(
        binding=binding2,
        id=2,
        best_datatype=False,
        data_usable=False,
        passing_replicate=False,
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"pk": 1},
        {"binding": binding1.id},
        {"best_datatype": True},
        {"data_usable": True},
        {"passing_replicate": True},
    ]

    # Apply each filter and check if it returns the expected bindings
    for params in filter_params:
        f = BindingManualQCFilter(params, queryset=BindingManualQC.objects.all())
        assert binding_manual_qc1 in f.qs
        assert binding_manual_qc2 not in f.qs


@pytest.mark.django_db
def test_datasource_filter():
    # Create some binding sources using the factory

    fileformat1 = FileFormatFactory(fileformat="fileformat1")
    fileformat2 = FileFormatFactory(fileformat="fileformat2")
    datasource1 = DataSourceFactory(
        id=1,
        fileformat=fileformat1,
        lab="lab1",
        assay="assay1",
        workflow="workflow1",
    )
    datasource2 = DataSourceFactory(
        id=2,
        fileformat=fileformat2,
        lab="lab2",
        assay="assay2",
        workflow="workflow2",
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"pk": 1},
        {"fileformat_id": fileformat1.id},
        {"fileformat": "fileformat1"},
        {"lab": "lab1"},
        {"assay": "assay1"},
        {"workflow": "workflow1"},
    ]

    # Apply each filter and check if it returns the expected binding sources
    for params in filter_params:
        f = DataSourceFilter(params, queryset=DataSource.objects.all())
        assert datasource1 in f.qs
        assert datasource2 not in f.qs


@pytest.mark.django_db
def test_calling_cards_background_filter():
    # Create some CallingCardsBackground instances using the factory
    background1 = CallingCardsBackgroundFactory(
        id=1,
        name="name1",
        genomic_inserts=10,
        mito_inserts=20,
        plasmid_inserts=30,
        notes="notes1",
    )
    background2 = CallingCardsBackgroundFactory(
        id=2,
        name="name2",
        genomic_inserts=40,
        mito_inserts=50,
        plasmid_inserts=60,
        notes="notes2",
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"name": "name1"},
    ]

    # Apply each filter and check if it returns the expected backgrounds
    for params in filter_params:
        f = CallingCardsBackgroundFilter(params, queryset=CallingCardsBackground.objects.all())
        assert background1 in f.qs
        assert background2 not in f.qs


@pytest.mark.django_db
def test_expression_filter():
    # Create some expressions using the factory
    regulator1 = RegulatorFactory()
    regulator2 = RegulatorFactory()
    source1 = DataSourceFactory()
    source2 = DataSourceFactory()
    expression1 = ExpressionFactory(
        regulator=regulator1,
        id=1,
        batch="batch1",
        replicate=1,
        control="undefined",
        mechanism="gev",
        restriction="P",
        time=1,
        source=source1,
    )
    expression2 = ExpressionFactory(
        regulator=regulator2,
        id=2,
        batch="batch2",
        replicate=2,
        control="wt",
        mechanism="zev",
        restriction="M",
        time=2,
        source=source2,
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"pk": 1},
        {"regulator": regulator1.id},
        {"regulator_locus_tag": regulator1.genomicfeature.locus_tag},
        {"regulator_symbol": regulator1.genomicfeature.symbol},
        {"batch": "batch1"},
        {"replicate": 1},
        {"control": "undefined"},
        {"mechanism": "gev"},
        {"restriction": "P"},
        {"time": 1},
        {"source": source1.id},
        {"lab": source1.lab},
        {"assay": source1.assay},
        {"workflow": source1.workflow},
    ]

    # Apply each filter and check if it returns the expected expressions
    for params in filter_params:
        f = ExpressionFilter(params, queryset=Expression.objects.all())
        assert expression1 in f.qs
        assert expression2 not in f.qs


@pytest.mark.django_db
def test_expression_manual_qc_filter():
    # Create some expressions using the factory
    regulator1 = RegulatorFactory()
    regulator2 = RegulatorFactory()
    source1 = DataSourceFactory()
    source2 = DataSourceFactory()
    expression1 = ExpressionFactory(
        regulator=regulator1,
        id=1,
        batch="batch1",
        replicate=1,
        control="undefined",
        mechanism="gev",
        restriction="P",
        time=1,
        source=source1,
    )
    expression2 = ExpressionFactory(
        regulator=regulator2,
        id=2,
        batch="batch2",
        replicate=2,
        control="wt",
        mechanism="zev",
        restriction="M",
        time=2,
        source=source2,
    )
    manual_qc1 = ExpressionManualQCFactory(id=1, expression=expression1, strain_verified="yes")
    manual_qc2 = ExpressionManualQCFactory(id=2, expression=expression2, strain_verified="no")

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"pk": 1},
        {"expression": expression1.id},
        {"strain_verified": manual_qc1.strain_verified},
        {"regulator_locus_tag": regulator1.genomicfeature.locus_tag},
        {"regulator_symbol": regulator1.genomicfeature.symbol},
        {"batch": expression1.batch},
        {"replicate": expression1.replicate},
        {"control": expression1.control},
        {"mechanism": expression1.mechanism},
        {"restriction": expression1.restriction},
        {"time": expression1.time},
        {"source": source1.id},
        {"lab": source1.lab},
        {"assay": source1.assay},
        {"workflow": source1.workflow},
    ]

    # Apply each filter and check if it returns the expected ExpressionManualQC instances
    for params in filter_params:
        f = ExpressionManualQCFilter(params, queryset=ExpressionManualQC.objects.all())
        assert manual_qc1 in f.qs
        assert manual_qc2 not in f.qs


@pytest.mark.django_db
def test_file_format_filter():
    # Create some FileFormat instances using the factory
    fileformat1 = FileFormatFactory(fileformat="fileformat1")
    fileformat2 = FileFormatFactory(fileformat="fileformat2")

    # Define the filter parameters and their expected values
    filter_params = [
        {"fileformat": "fileformat1"},
    ]

    # Apply each filter and check if it returns the expected FileFormat instances
    for params in filter_params:
        f = FileFormatFilter(params, queryset=FileFormat.objects.all())
        assert fileformat1 in f.qs
        assert fileformat2 not in f.qs


@pytest.mark.django_db
def test_genomic_feature_filter():
    # Create some GenomicFeature instances using the factory
    chr1 = ChrMapFactory(ucsc="chr1")
    chr2 = ChrMapFactory(ucsc="chr2")
    genomic_feature1 = GenomicFeatureFactory(
        chr=chr1,
        start=1,
        end=100,
        strand="+",
        type="type1",
        locus_tag="tag1",
        symbol="gene1",
        source="source1",
        alias="alias1",
        note="note1",
    )
    genomic_feature2 = GenomicFeatureFactory(
        chr=chr2,
        start=101,
        end=200,
        strand="-",
        type="type2",
        locus_tag="tag2",
        symbol="gene2",
        source="source2",
        alias="alias2",
        note="note2",
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"chr": "chr1"},
        {"start": 1},
        {"end": 100},
        {"strand": "+"},
        {"type": "type1"},
        {"locus_tag": "tag1"},
        {"symbol": "gene1"},
        {"source": "source1"},
        {"alias": "alias1"},
        {"note": "note1"},
    ]

    # Apply each filter and check if it returns the expected GenomicFeature instances
    for params in filter_params:
        f = GenomicFeatureFilter(params, queryset=GenomicFeature.objects.all())
        assert genomic_feature1 in f.qs
        assert genomic_feature2 not in f.qs


@pytest.mark.django_db
def test_promoter_set_filter():
    # Create some PromoterSet instances using the factory
    promoter_set1 = PromoterSetFactory(name="set1")
    promoter_set2 = PromoterSetFactory(name="set2")

    # Define the filter parameters and their expected values
    filter_params = [
        {"name": promoter_set1.name},
    ]

    # Apply each filter and check if it returns the expected PromoterSet instances
    for params in filter_params:
        f = PromoterSetFilter(params, queryset=PromoterSet.objects.all())
        assert promoter_set1 in f.qs
        assert promoter_set2 not in f.qs


@pytest.mark.django_db
def test_promoter_set_sig_filter():
    # Create some PromoterSetSig instances using the factory
    regulator1 = RegulatorFactory()
    regulator2 = RegulatorFactory()
    promoter1 = PromoterSetFactory(name="promoter1")
    promoter2 = PromoterSetFactory(name="promoter2")
    background1 = CallingCardsBackgroundFactory(name="bg1")
    background2 = CallingCardsBackgroundFactory(name="bg2")
    datasource1 = DataSourceFactory(lab="lab1", assay="assay1", workflow="workflow1")
    datasource2 = DataSourceFactory(lab="lab2", assay="assay2", workflow="workflow2")
    binding1 = BindingFactory(regulator=regulator1, batch="batch1", replicate=1, source=datasource1)
    binding2 = BindingFactory(regulator=regulator2, batch="batch2", replicate=2, source=datasource2)
    promoter_set_sig1 = PromoterSetSigFactory(id=1, binding=binding1, promoter=promoter1, background=background1)
    promoter_set_sig2 = PromoterSetSigFactory(id=2, binding=binding2, promoter=promoter2, background=background2)

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": promoter_set_sig1.id},
        {"pk": promoter_set_sig1.pk},
        {"binding": binding1.id},
        {"promoter": promoter1.id},
        {"promoter_name": "promoter1"},
        {"background": background1.id},
        {"background_name": background1.name},
        {"regulator_locus_tag": regulator1.genomicfeature.locus_tag},
        {"regulator_symbol": regulator1.genomicfeature.symbol},
        {"batch": "batch1"},
        {"replicate": 1},
        {"source": datasource1.id},
        {"lab": "lab1"},
        {"assay": "assay1"},
        {"workflow": "workflow1"},
    ]

    # Apply each filter and check if it returns the expected PromoterSetSig instances
    for params in filter_params:
        f = PromoterSetSigFilter(params, queryset=PromoterSetSig.objects.all())
        assert promoter_set_sig1 in f.qs
        assert promoter_set_sig2 not in f.qs


@pytest.mark.django_db
def test_rankresponse_filter():
    # Create some RankResponse instances using the factory
    genomicfeature1 = GenomicFeatureFactory(locus_tag="tag1", symbol="symbol1")
    genomicfeature2 = GenomicFeatureFactory(locus_tag="tag2", symbol="symbol2")
    regulator1 = RegulatorFactory(genomicfeature=genomicfeature1)
    regulator2 = RegulatorFactory(genomicfeature=genomicfeature2)
    binding1 = BindingFactory(regulator=regulator1)
    binding2 = BindingFactory(regulator=regulator2)
    promotersetsig1 = PromoterSetSigFactory(binding=binding1)
    promotersetsig2 = PromoterSetSigFactory(binding=binding2)
    expression1 = ExpressionFactory(regulator=regulator1)
    expression2 = ExpressionFactory(regulator=regulator2)

    rankresponse1 = RankResponseFactory(
        id=1,
        promotersetsig=promotersetsig1,
        expression=expression1,
    )
    rankresponse2 = RankResponseFactory(
        id=2,
        promotersetsig=promotersetsig2,
        expression=expression2,
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"regulator_locus_tag": promotersetsig1.binding.regulator.genomicfeature.locus_tag},
        {"regulator_symbol": promotersetsig1.binding.regulator.genomicfeature.symbol},
        {"binding_source": promotersetsig1.binding.source.name},
        {"expression_source": expression1.source.name},
    ]

    # Apply each filter and check if it returns the expected RankResponse instances
    for params in filter_params:
        f = RankResponseFilter(params, queryset=RankResponse.objects.all())
        assert rankresponse1 in f.qs
        assert rankresponse2 not in f.qs


@pytest.mark.django_db
def test_regulator_filter():
    # Create some Regulator instances using the factory
    regulator1 = RegulatorFactory(
        id=1, genomicfeature__locus_tag="tag1", genomicfeature__symbol="symbol1", under_development=True
    )
    regulator2 = RegulatorFactory(
        id=2, genomicfeature__locus_tag="tag2", genomicfeature__symbol="symbol2", under_development=False
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"pk": 1},
        {"regulator_locus_tag": "tag1"},
        {"regulator_symbol": "symbol1"},
        {"under_development": True},
    ]

    # Apply each filter and check if it returns the expected Regulator instances
    for params in filter_params:
        f = RegulatorFilter(params, queryset=Regulator.objects.all())
        assert regulator1 in f.qs
        assert regulator2 not in f.qs
