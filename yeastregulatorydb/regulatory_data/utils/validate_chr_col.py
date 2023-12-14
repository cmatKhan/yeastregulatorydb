import pandas as pd

from ..models.ChrMap import ChrMap


def validate_chr_col(df: pd.DataFrame, chrmap_field: str) -> bool:
    """
    Check if all unique values in df['chr'] are contained in at least one of
        the fields of the chrmap table.

        :param df: a pandas dataframe of the bed file
        :type df: pd.DataFrame
        :param chrmap_field: the field in ChrMap to check
        :type chrmap_field: str

        :return: True if all unique values in df['chr'] are contained in at least
            one of the fields of the chrmap table
        :rtype: bool

        :raises TypeError: if df is not a pandas DataFrame or chrmap_field is not a string
        :raises ValueError: if chrmap_field is not a valid field in ChrMap
        :raises AttributeError: if the chromosome names in the file do not match
            at least one of the fields in ChrMap
    """
    # check input types
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(chrmap_field, str):
        raise TypeError("chrmap_field must be a string")

    # check that chrmap_field is a valid field in ChrMap
    if "chr" not in df.columns:
        raise ValueError("The DataFrame does not have a column `chr`.")

    # check that the chromosome names in the file match at least one of the
    # fields in ChrMap
    chr_values_set = set(df.chr.unique())
    chrmap_records = ChrMap.objects.all()
    chrmap_values = {getattr(record, chrmap_field) for record in chrmap_records}
    if not chr_values_set.issubset(chrmap_values):
        raise AttributeError(
            f"The following chromosomes in the uploaded file "
            f"do not match any chromosomes in the database "
            f"for field {chrmap_field}: "
            f"{chr_values_set - chrmap_values}"
        )

    # Check if 'start' is less than or equal to 'end'
    if any(df["start"] > df["end"]):
        raise ValueError("`start` should always be before `end`. there exists " "a row for which this is not true.")

    # check that the min/max coordinates for each chromosome do not exceed the
    # chr bounds
    agg_func = {"start": "min", "end": "max"}
    grouped_df = df.groupby("chr", as_index=False).agg(agg_func)
    chrmap_queryset = chrmap_records.values(chrmap_field, "seqlength")

    # Convert the QuerySet to a dictionary
    chrmap_dict = {row[chrmap_field]: row["seqlength"] for row in chrmap_queryset}

    invalid_coordinates = []
    for row in grouped_df.itertuples(index=False):
        chr_seqlength = chrmap_dict.get(row[0])
        if chr_seqlength is not None:
            chr_seqlength = int(chr_seqlength)

            if int(row[1]) < 0:
                invalid_coordinates.append((row[0], row[1]))
            if int(row[2]) > chr_seqlength + 1:
                invalid_coordinates.append((row[0], row[2]))
        else:
            invalid_coordinates.append((row[0], "Unknown chromosome"))

    if invalid_coordinates:
        raise AttributeError(
            f"The following coordinates in the uploaded file "
            f"exceed the bounds of the corresponding chromosome "
            f"for field {chrmap_field}: "
            f"{invalid_coordinates}"
        )

    return True
