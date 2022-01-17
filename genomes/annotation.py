"""Contains tools for processing annotation sheets."""

import pandas as pd
from collections import Counter
from core.models import User
from genomes.data import SPECIES, CELL_LINES, METHODS

REQUIRED_COLUMNS = [
    "Collection Name",
    "Scientist",
    "PI",
    "Method",
    "Pipeline",
    "Protein",
    "Cell or Tissue",
    "Species",
    "5' Barcode",
    "3' Adapter Sequence",
    "Sequencer",
    "Purification Method (Antibody)",
]  

def validate_uploaded_sheet(upload):
    try:
        df = parse_upload(upload)
    except: return "Could not read file - ensure it is valid CSV or valid Excel"

    problems = []

    # Missing columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        problems.append(f"The following required columns were not found: {', '.join(missing_columns)}")

    # Required columns not filled in?
    for i in range(len(df)):
        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                value = df.loc[i, col]
                if not value or pd.isna(value):
                    problems.append(f"Row {i + 1} is missing a value for required column '{col}'")
    
    # Sample names unique?
    sample_names = df["Sample Name (Optional)"].values
    counter = Counter(sample_names)
    for name, count in counter.items():
        if count > 1:
            problems.append(f"{count} rows have the same sample name: {name}")
    
    # Usernames valid?
    for i in range(len(df)):
        username = df.loc[i, "Scientist"]
        pi = df.loc[i, "PI"]
        if not User.objects.filter(username=username):
            problems.append(f"There is no user with username '{username}' (Row {i + 1}, Scientist)")
        if not User.objects.filter(username=pi):
            problems.append(f"There is no user with username '{pi}' (Row {i + 1}, PI)")
    
    # DNA valid?
    dna_columns = ["5' Barcode", "3' Barcode", "3' Adapter Sequence"]
    for i in range(len(df)):
        for column in df.columns:
            for dna_column in dna_columns:
                if dna_column in column:
                    value = df.loc[i, column]
                    if value and not pd.isna(value):
                        if not isinstance(value, str) or any(c not in "GCATN" for c in value):
                            problems.append(
                                f"'{value}' is not valid DNA (Row {i + 1}, {column})"
                            )
    
    # Method valid?
    for i in range(len(df)):
        method = df.loc[i, "Method"]
        if method and not pd.isna(method) and method not in METHODS:
            problems.append(f"'{method}' is not a valid method (Row {i + 1})")
    
    # Species valid?
    for i in range(len(df)):
        species = df.loc[i, "Species"]
        if species and not pd.isna(species) and species not in SPECIES:
            problems.append(f"'{species}' is not a valid species (Row {i + 1})")
    
    # Cell line valid?
    for i in range(len(df)):
        cells = df.loc[i, "Cell or Tissue"]
        if cells and not pd.isna(cells) and cells not in CELL_LINES:
            problems.append(f"'{cells}' is not a valid cell line (Row {i + 1})")

    

    return problems


    
    # Check gene is valid
    # Check collection existence
    # Check collection name validity
    # Check sample name validity


def parse_upload(upload):
    try:
        return pd.read_csv(upload)
    except:
        upload.seek(0)
        return pd.read_excel(upload)