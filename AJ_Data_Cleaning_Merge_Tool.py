import pandas as pd
import streamlit as st
from io import BytesIO
import numpy as np


# -------------------------
# Reset Report Function
# -------------------------
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
        "numeric_converted": 0
    }


# -------------------------
# File Reader
# -------------------------
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
            st.error(f"Unsupported file extension: .{ext}")
            return None

    except Exception as e:
        st.error(f"File reading error: {e}")
        return None


# -------------------------
# Cleaning Functions
# -------------------------
def clean_column(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.title()
        .str.replace(" ", "_", regex=True)
    )
    return df


def remove_empty_rows_columns(df, report):
    row_before, col_before = df.shape

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    row_after, col_after = df.shape

    report["empty_rows_removed"] = row_before - row_after
    report["empty_cols_removed"] = col_before - col_after

    return df


def remove_duplicates(df, report):
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)
    return df


def trim_string_spaces(df, report):
    extra_spaces = 0
    object_cols = df.select_dtypes(include="object").columns

    for col in object_cols:
        before = df[col].copy()
        df[col] = df[col].str.strip()
        extra_spaces += ((before != df[col]) & before.notna()).sum()

    report["spaces_trimmed"] = extra_spaces
    return df


def clean_numeric_strings(df, report):
    object_cols = df.select_dtypes(include="object").columns

    for col in object_cols:
        if df[col].astype(str).str.contains(r"[,$€₹%]", regex=True).any():

            cleaned = (
                df[col]
                .astype(str)
                .str.replace(r"[,$€₹% ]", "", regex=True)
            )

            converted = pd.to_numeric(cleaned, errors="coerce")

            if converted.notna().sum() > 0:
                df[col] = converted
                report["numeric_converted"] += 1

    return df


# -------------------------
# Merge Functions
# -------------------------
def get_common_column(df1, df2):
    common = list(df1.columns.intersection(df2.columns))

    if not common:
        st.error("No common columns found. Cannot merge!")
        st.stop()

    return common


def perform_merge(df1, df2, on_column, merge_type):
    return pd.merge(df1, df2, on=on_column, how=merge_type)


# -------------------------
# Download Functions
# -------------------------
def download_file(df, filename_prefix):
    option = st.radio("Choose file format:", ("csv", "excel", "json"))

    if option == "csv":
        data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data, f"{filename_prefix}.csv")

    elif option == "excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            "Download Excel",
            output.getvalue(),
            f"{filename_prefix}.xlsx"
        )

    elif option == "json":
        data = df.to_json(orient="records", indent=4).encode("utf-8")
        st.download_button("Download JSON", data, f"{filename_prefix}.json")


# -------------------------
# MAIN APP
# -------------------------
def main():

    st.set_page_config(page_title="AJ_Tech_Tool", layout="wide")
    st.title("🚀 AJ – Intelligent Data Cleaning & Merge Tool")

    tool = st.sidebar.selectbox(
        "Choose Operation",
        ["Welcome Dashboard", "Data Cleaning", "Data Merge"]
    )

    # ------------------ WELCOME ------------------
    if tool == "Welcome Dashboard":
        st.info("Select a tool from sidebar to begin.")

    # ------------------ CLEANING ------------------
    elif tool == "Data Cleaning":

        report = init_report()

        file = st.file_uploader("Upload Dataset",
                                type=["csv", "xlsx", "json"])

        if file:

            with st.spinner("Reading file..."):
                df = read_file(file)

            if df is None:
                return

            report["rows_before"] = df.shape[0]
            report["cols_before"] = df.shape[1]

            progress = st.progress(0)

            df = clean_column(df)
            progress.progress(20)

            df = trim_string_spaces(df, report)
            progress.progress(40)

            df = remove_duplicates(df, report)
            progress.progress(60)

            df = clean_numeric_strings(df, report)
            progress.progress(80)

            df = remove_empty_rows_columns(df, report)
            progress.progress(100)

            report["rows_after"] = df.shape[0]
            report["cols_after"] = df.shape[1]

            st.success("Data Cleaning Completed Successfully!")

            st.subheader("Cleaned Data")
            st.dataframe(df, use_container_width=True)

            st.subheader("Cleaning Report")

            col1, col2 = st.columns(2)

            col1.metric("Rows Removed",
                        report["rows_before"] - report["rows_after"])
            col1.metric("Duplicates Removed",
                        report["duplicates_removed"])

            col2.metric("Columns Removed",
                        report["cols_before"] - report["cols_after"])
            col2.metric("Spaces Trimmed",
                        report["spaces_trimmed"])

            st.metric("Numeric Columns Converted",
                      report["numeric_converted"])

            st.subheader("Download Cleaned File")
            download_file(df, "cleaned_data")

    # ------------------ MERGE ------------------
    elif tool == "Data Merge":

        file1 = st.file_uploader("First file",
                                 type=["csv", "json", "xlsx"])
        file2 = st.file_uploader("Second file",
                                 type=["csv", "json", "xlsx"])

        if file1 and file2:

            with st.spinner("Reading files..."):
                df1 = read_file(file1)
                df2 = read_file(file2)

            if df1 is None or df2 is None:
                return

            df1 = clean_column(df1)
            df2 = clean_column(df2)

            common = get_common_column(df1, df2)

            on_column = st.selectbox("Merge On", common)
            merge_type = st.selectbox(
                "Merge Type",
                ["inner", "outer", "left", "right"]
            )

            merged_df = perform_merge(
                df1, df2, on_column, merge_type
            )

            st.success("Merge Completed Successfully!")

            st.write(f"Shape: {merged_df.shape}")
            st.dataframe(merged_df.head(10),
                         use_container_width=True)

            st.subheader("Download Merged File")
            download_file(merged_df, "merged_data")


main()
