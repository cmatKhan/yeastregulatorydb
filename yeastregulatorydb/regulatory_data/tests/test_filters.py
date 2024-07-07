import pytest

from yeastregulatorydb.regulatory_data.api.filters import (
    BindingConcatenatedFilter,
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
    RegulatorFilter,
)
from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingConcatenated,
    BindingManualQC,
    CallingCardsBackground,
    DataSource,
    Expression,
    ExpressionManualQC,
    FileFormat,
    GenomicFeature,
    PromoterSet,
    PromoterSetSig,
    Regulator,
)

from .factories import (
    BindingConcatenatedFactory,
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
    PromoterSetSigWithCompositeBindingFactory,
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
def test_binding_concatenated_filter():
    # Create regulators and data sources
    regulator1 = RegulatorFactory()
    regulator2 = RegulatorFactory()
    source1 = DataSourceFactory()
    source2 = DataSourceFactory()

    # Create bindings
    binding1 = BindingFactory(regulator=regulator1, source=source1)
    binding2 = BindingFactory(regulator=regulator1, source=source1)
    binding3 = BindingFactory(regulator=regulator2, source=source2)
    binding4 = BindingFactory(regulator=regulator2, source=source2)

    # Create BindingConcatenated instances
    concatenated1 = BindingConcatenatedFactory(regulator=regulator1, source=source1, bindings=[binding1, binding2])

    concatenated2 = BindingConcatenatedFactory(regulator=regulator2, source=source2, bindings=[binding3, binding4])

    # Define filter parameters
    filter_params = {
        "regulator": regulator1.id,
    }

    # Apply the filter
    filter_set = BindingConcatenatedFilter(filter_params, queryset=BindingConcatenated.objects.all())
    filtered_qs = filter_set.qs

    # Assertions
    assert concatenated1 in filtered_qs
    assert concatenated2 not in filtered_qs

    # Define filter parameters for source
    filter_params = {
        "source": source1.id,
    }

    # Apply the filter
    filter_set = BindingConcatenatedFilter(filter_params, queryset=BindingConcatenated.objects.all())
    filtered_qs = filter_set.qs

    # Assertions
    assert concatenated1 in filtered_qs
    assert concatenated2 not in filtered_qs


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
        single_binding=binding1,
        id=1,
        best_datatype="pass",
        data_usable="pass",
        passing_replicate="pass",
    )
    binding_manual_qc2 = BindingManualQCFactory(
        single_binding=binding2,
        id=2,
        best_datatype="fail",
        data_usable="unreviewed",
        passing_replicate="fail",
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
        {"single_binding": binding1.id},
        {"best_datatype": "pass"},
        {"data_usable": "pass"},
        {"passing_replicate": "pass"},
    ]

    # Apply each filter and check if it returns the expected bindings
    for params in filter_params:
        f = BindingManualQCFilter(params, queryset=BindingManualQC.objects.all())
        assert binding_manual_qc1 in f.qs, f"error params: {params}"
        assert binding_manual_qc2 not in f.qs, f"error params: {params}"


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
        id=1,
        regulator=regulator1,
        batch="batch1",
        replicate=1,
        control="undefined",
        mechanism="gev",
        restriction="P",
        time=1,
        source=source1,
    )
    expression2 = ExpressionFactory(
        id=2,
        regulator=regulator2,
        batch="batch2",
        replicate=2,
        control="wt",
        mechanism="zev",
        restriction="M",
        time=2,
        source=source2,
    )
    expression3 = ExpressionFactory(
        id=3,
        regulator=regulator1,
        batch="batch1",
        replicate=1,
        control="undefined",
        mechanism="gev",
        restriction="P",
        time=3,
        source=source1,
    )

    # Define the filter parameters and their expected values
    filter_params = [
        {"id": 1},
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
        {"source_time": f"{source1.name},{expression1.time}"},
        {"lab": source1.lab},
        {"assay": source1.assay},
        {"workflow": source1.workflow},
    ]

    # Apply each filter and check if it returns the expected expressions
    for params in filter_params:
        f = ExpressionFilter(params, queryset=Expression.objects.all())
        filtered_qs = f.qs
        if params.get("source_time"):
            assert expression1 in filtered_qs
            assert expression2 in filtered_qs
            assert expression3 not in filtered_qs
        else:
            assert expression1 in filtered_qs
            assert expression2 not in filtered_qs


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
        {"expression": expression1.id},
        {"strain_verified": manual_qc1.strain_verified},
        {"regulator_locus_tag": regulator1.genomicfeature.locus_tag},
        {"regulator_symbol": regulator1.genomicfeature.symbol},
        {"time": expression1.time},
        {"source": source1.id},
        {"lab": source1.lab},
        {"assay": source1.assay},
        {"workflow": source1.workflow},
    ]

    # Apply each filter and check if it returns the expected ExpressionManualQC instances
    for params in filter_params:
        f = ExpressionManualQCFilter(params, queryset=ExpressionManualQC.objects.all())
        assert manual_qc1 in f.qs, params
        assert manual_qc2 not in f.qs, params


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
        {"start_min": 1, "start_max": 50},  # Test range filter for start
        {"end_min": 50, "end_max": 150},  # Test range filter for end
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
        assert genomic_feature1 in f.qs, f"Failed for filter params: {params}"
        assert genomic_feature2 not in f.qs, f"Failed for filter params: {params}"

    # Additional test cases for range filters
    range_filter_params = [
        {"start_min": 0, "start_max": 200},  # Both genomic_feature1 and genomic_feature2 should be included
        {"end_min": 1, "end_max": 150},  # Only genomic_feature1 should be included
    ]

    # Apply each range filter and check the expected results
    for params in range_filter_params:
        f = GenomicFeatureFilter(params, queryset=GenomicFeature.objects.all())
        if "start_min" in params or "start_max" in params:
            assert genomic_feature1 in f.qs, f"Failed for range filter params: {params}"
        if params.get("start_max", None) == 200:
            assert genomic_feature2 in f.qs, f"Failed for range filter params: {params}"
        else:
            assert genomic_feature2 not in f.qs, f"Failed for range filter params: {params}"
        if "end_min" in params or "end_max" in params:
            assert genomic_feature1 in f.qs, f"Failed for range filter params: {params}"
            assert genomic_feature2 not in f.qs, f"Failed for range filter params: {params}"


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
    binding2 = BindingFactory(regulator=regulator1, batch="batch2", replicate=2, source=datasource1)

    # Use the updated factory for single binding
    promoter_set_sig1 = PromoterSetSigFactory(
        id=1, single_binding=binding1, promoter=promoter1, background=background2
    )
    promoter_set_sig2 = PromoterSetSigFactory(
        id=2, single_binding=binding2, promoter=promoter2, background=background1
    )

    # Test composite binding case
    binding3 = BindingFactory(regulator=regulator2, batch="batch3", replicate=1, source=datasource2)
    binding4 = BindingFactory(regulator=regulator2, batch="batch4", replicate=2, source=datasource2)
    composite_binding = BindingConcatenatedFactory(
        regulator=regulator2, source=datasource2, bindings=[binding3, binding4]
    )

    promoter_set_sig3 = PromoterSetSigWithCompositeBindingFactory(
        id=3, composite_binding=composite_binding, promoter=promoter1, background=background1
    )

    # Define the filter parameters and their expected results
    filter_tests = [
        {
            "params": {"id": promoter_set_sig1.id},
            "expected": [promoter_set_sig1],
            "unexpected": [promoter_set_sig2, promoter_set_sig3],
        },
        {
            "params": {"single_binding": binding1.id},
            "expected": [promoter_set_sig1],
            "unexpected": [promoter_set_sig2, promoter_set_sig3],
        },
        {
            "params": {"promoter": promoter1.id},
            "expected": [promoter_set_sig1, promoter_set_sig3],
            "unexpected": [promoter_set_sig2],
        },
        {
            "params": {"promoter_name": "promoter1"},
            "expected": [promoter_set_sig1, promoter_set_sig3],
            "unexpected": [promoter_set_sig2],
        },
        {
            "params": {"background": background1.id},
            "expected": [promoter_set_sig2, promoter_set_sig3],
            "unexpected": [promoter_set_sig1],
        },
        {
            "params": {"background_name": "bg1"},
            "expected": [promoter_set_sig2, promoter_set_sig3],
            "unexpected": [promoter_set_sig1],
        },
        {
            "params": {"regulator_locus_tag": regulator1.genomicfeature.locus_tag},
            "expected": [promoter_set_sig1, promoter_set_sig2],
            "unexpected": [promoter_set_sig3],
        },
        {
            "params": {"regulator_symbol": regulator1.genomicfeature.symbol},
            "expected": [promoter_set_sig1, promoter_set_sig2],
            "unexpected": [promoter_set_sig3],
        },
        {
            "params": {"batch": "batch1"},
            "expected": [promoter_set_sig1],
            "unexpected": [promoter_set_sig2, promoter_set_sig3],
        },
        {
            "params": {"source": datasource1.id},
            "expected": [promoter_set_sig1, promoter_set_sig2],
            "unexpected": [promoter_set_sig3],
        },
        {
            "params": {"lab": "lab1"},
            "expected": [promoter_set_sig1, promoter_set_sig2],
            "unexpected": [promoter_set_sig3],
        },
        {
            "params": {"assay": "assay1"},
            "expected": [promoter_set_sig1, promoter_set_sig2],
            "unexpected": [promoter_set_sig3],
        },
        {
            "params": {"workflow": "workflow1"},
            "expected": [promoter_set_sig1, promoter_set_sig2],
            "unexpected": [promoter_set_sig3],
        },
    ]

    for test in filter_tests:
        params = test["params"]
        f = PromoterSetSigFilter(params, queryset=PromoterSetSig.objects.all())
        for expected_instance in test["expected"]:
            assert (
                expected_instance in f.qs
            ), f"Expected instance {expected_instance} not found for filter params: {params}"
        for unexpected_instance in test["unexpected"]:
            assert (
                unexpected_instance not in f.qs
            ), f"Unexpected instance {unexpected_instance} found for filter params: {params}"


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
        {"regulator_locus_tag": "tag1"},
        {"regulator_symbol": "symbol1"},
        {"under_development": True},
    ]

    # Apply each filter and check if it returns the expected Regulator instances
    for params in filter_params:
        f = RegulatorFilter(params, queryset=Regulator.objects.all())
        assert regulator1 in f.qs
        assert regulator2 not in f.qs
