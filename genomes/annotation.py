"""Contains tools for processing annotation sheets."""

import pandas as pd
from collections import Counter
from django.core.exceptions import ValidationError
from core.models import User
from analysis.models import Collection, Sample
from core.permissions import does_user_have_permission_on_collection
from genomes.data import SPECIES, CELL_LINES, METHODS
from genomes.models import Gene

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

def validate_uploaded_sheet(upload, user, ignore_warnings=False):
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
    if "Sample Name (Optional)" in df.columns:
        sample_names = df["Sample Name (Optional)"].values
        counter = Counter(sample_names)
        for name, count in counter.items():
            if count > 1:
                problems.append(f"{count} rows have the same sample name: {name}")
    
    # Sample names valid?
    if "Sample Name (Optional)" in df.columns:
        name_validators = [field for field in Sample._meta.fields if field.name == "name"][0].validators
        for i in range(len(df)):
            sample_name = df.loc[i, "Sample Name (Optional)"]
            for validator in name_validators:
                try:
                    validator(sample_name)
                except ValidationError as e:
                    problems.append(f"Sample name '{sample_name}' (Row {i + 1}) doesn't validate: '{e.messages[0]}'")
    
    # Collection names valid?
    if "Collection Name" in df.columns:
        name_validators = [field for field in Collection._meta.fields if field.name == "name"][0].validators
        for i in range(len(df)):
            collection_name = df.loc[i, "Collection Name"]
            for validator in name_validators:
                try:
                    validator(collection_name)
                except ValidationError as e:
                    problems.append(f"Collection name '{collection_name}' (Row {i + 1}) doesn't validate: '{e.messages[0]}'")

    # Usernames valid?
    if "Scientist" in df.columns and "PI" in df.columns:
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
    if "Method" in df.columns:
        for i in range(len(df)):
            method = df.loc[i, "Method"]
            if method and not pd.isna(method) and method not in METHODS:
                problems.append(f"'{method}' is not a valid method (Row {i + 1})")
    
    # Species valid?
    if "Species" in df.columns:
        for i in range(len(df)):
            species = df.loc[i, "Species"]
            if species and not pd.isna(species) and species not in SPECIES:
                problems.append(f"'{species}' is not a valid species (Row {i + 1})")
    
    # Cell line valid?
    if "Cell or Tissue" in df.columns:
        for i in range(len(df)):
            cells = df.loc[i, "Cell or Tissue"]
            if cells and not pd.isna(cells) and cells not in CELL_LINES:
                problems.append(f"'{cells}' is not a valid cell line (Row {i + 1})")
    
    # Protein valid?
    if "Protein" in df.columns and "Species" in df.columns:
        for i in range(len(df)):
            protein = df.loc[i, "Protein"]
            species = df.loc[i, "Species"]
            if protein and not pd.isna(protein) and species and not pd.isna(species) and species in SPECIES:
                gene = Gene.objects.filter(species=species, name=protein).first()
                if not gene:
                    problems.append(f"'{protein}' is not a valid protein for species '{species}' (Row {i + 1})")

    # Check collection name access
    warning_collection_names = set()
    if "Collection Name" in df.columns:
        for i in range(len(df)):
            collection_name = df.loc[i, "Collection Name"]
            collection = Collection.objects.filter(name=collection_name).first()
            if collection:
                if does_user_have_permission_on_collection(user, collection, 2):
                    warning_collection_names.add(collection.name)
                else:
                    problems.append(f"Collection with name '{collection_name}' already exists and you don't have permission to modify it Row {i + 1})")
    if warning_collection_names and not problems and not ignore_warnings:
        return problems, f"The following collections already exist, and would have samples added to them if you use this annotation spreadsheet: {', '.join(warning_collection_names)}."
    return problems, ""


    
    # Check collection existence


def parse_upload(upload):
    try:
        return pd.read_csv(upload)
    except:
        upload.seek(0)
        return pd.read_excel(upload)