import pandas as pd
import streamlit as st
from io import BytesIO

# ------------------------------
# CONFIG
# ------------------------------
st.set_page_config(page_title="AJ_Tech_Tool", layout="wide")

# ------------------------------
# REPORT RESET FUNCTION
# ------------------------------
def init_report():
    return {
        "rows_before": 0,
        "rows_after": 0,
        "cols_before": 0,
        "cols_after": 0,
        "empty_rows_removed": 0,
        "empty_cols_removed": 0,
        "duplicates_removed": 0,
        "spaces_trimmed": 0,
    }

# ------------------------------
# FILE READER (CACHED)
# ------------------------------
@st.cache_data
def read_file(file):
    try:
        file_map = {
            "csv": pd.read_csv,
            "json": pd.read_json,
            "xlsx": pd.read_excel,
            "xls": pd.read_excel,
        }

        ext = file.name.split(".")[-1].lower()

        if ext in file_map:
            return file_map[ext](file)
        else:
            return None
    except Exception:
        return None

# ------------------------------
# CLEANING FUNCTIONS
# ------------------------------
def clean_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.title()
        .str.replace(" ", "_", regex=True)
    )
    return df


def trim_string_spaces(df, report):
    extra_spaces = 0
    obj_cols = df.select_dtypes(include="object").columns

    for col in obj_cols:
        before = df[col].copy()
        df[col] = df[col].str.strip()
        extra_spaces += ((before != df[col]) & before.notna()).sum()

    report["spaces_trimmed"] = int(extra_spaces)
    return df


def remove_duplicates(df, report):
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)
    return df


def clean_numeric_strings(df):
    obj_cols = df.select_dtypes(include="object").columns

    for col in obj_cols:
        cleaned = (
            df[col]
            .astype(str)
            .str.replace(r"[,$₹% ]", "", regex=True)
            .replace(["nan", "None", ""], pd.NA)
        )

        converted = pd.to_numeric(cleaned, errors="coerce")

        # Convert only if 70%+ values valid
        if converted.notna().sum() >= len(df) * 0.7:
            df[col] = converted

    return df


def remove_empty(df, report):
    rows_before, cols_before = df.shape

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    rows_after, cols_after = df.shape

    report["empty_rows_removed"] = rows_before - rows_after
    report["empty_cols_removed"] = cols_before - cols_after

    return df


# ------------------------------
# DOWNLOAD HELPERS
# ------------------------------
def download_cleaned(df):
    option = st.radio(
        "Choose file format",
        ("CSV", "Excel", "JSON"),
        key="clean_download",
    )

    if option == "CSV":
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "cleaned_data.csv",
            "text/csv",
        )

    elif option == "Excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            "Download Excel",
            output.getvalue(),
            "cleaned_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    elif option == "JSON":
        st.download_button(
            "Download JSON",
            df.to_json(orient="records", indent=4).encode("utf-8"),
            "cleaned_data.json",
            "application/json",
        )


def download_merged(df):
    option = st.radio(
        "Choose file format",
        ("CSV", "Excel", "JSON"),
        key="merge_download",
    )

    if option == "CSV":
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "merged_data.csv",
            "text/csv",
        )

    elif option == "Excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            "Download Excel",
            output.getvalue(),
            "
