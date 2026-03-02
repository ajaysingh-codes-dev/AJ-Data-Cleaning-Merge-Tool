import pandas as pd
import streamlit as st
from io import BytesIO


# ==============================
# Utility: Reset Cleaning Report
# ==============================

def reset_report():
    return {
        "rows_before": 0,
        "rows_after": 0,
        "cols_before": 0,
        "cols_after": 0,
        "empty_rows_removed": 0,
        "empty_cols_removed": 0,
        "duplicates_removed": 0,
        "spaces_trimmed": 0,
        "numeric_converted": []
    }


# ==============================
# File Reader
# ==============================

def read_file(file):
    try:
        readers = {
            "csv": pd.read_csv,
            "json": pd.read_json,
            "xlsx": pd.read_excel,
            "xls": pd.read_excel,
        }

        ext = file.name.split(".")[-1].lower()

        if ext in readers:
            return readers[ext](file)
        else:
            st.error(f"Unsupported file format: .{ext}")
            return None

    except Exception as e:
        st.error(f"File reading error: {e}")
        return None


# ==============================
# Cleaning Functions
# ==============================

def clean_column_names(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.title()
        .str.replace(" ", "_", regex=True)
    )
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


def remove_duplicates(df, report):
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)
    return df


def clean_numeric_strings(df, report):
    object_cols = df.select_dtypes(include="object").columns

    for col in object_cols:
        cleaned = (
            df[col]
            .astype(str)
            .str.replace(r"[,$₹% ]", "", regex=True)
            .replace(['nan', 'None', ''], pd.NA)
        )

        converted = pd.to_numeric(cleaned, errors="coerce")

        # Convert only if majority values are numeric
        if converted.notna().sum() > len(df) * 0.6:
            df[col] = converted
            report["numeric_converted"].append(col)

    return df


def remove_empty_rows_cols(df, report):
    row_before, col_before = df.shape

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    row_after, col_after = df.shape

    report["empty_rows_removed"] = row_before - row_after
    report["empty_cols_removed"] = col_before - col_after

    return df


def optimize_dtypes(df):
    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    return df


def run_cleaning_pipeline(df):
    report = reset_report()

    report["rows_before"] = df.shape[0]
    report["cols_before"] = df.shape[1]

    df = clean_column_names(df)
    df = trim_string_spaces(df, report)
    df = remove_duplicates(df, report)
    df = clean_numeric_strings(df, report)
    df = remove_empty_rows_cols(df, report)
    df = optimize_dtypes(df)

    report["rows_after"] = df.shape[0]
    report["cols_after"] = df.shape[1]

    return df, report


# ==============================
# Download Function
# ==============================

def download_file(df, filename_prefix="data"):
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


# ==============================
# Merge Logic
# ==============================

def perform_merge(df1, df2, column, merge_type):
    return pd.merge(df1, df2, on=column, how=merge_type)


# ==============================
# Main App
# ==============================

def main():
    st.set_page_config(page_title="AJ Tech Tool", layout="wide")
    st.title("🚀 AJ – Intelligent Data Tool")

    tool = st.sidebar.selectbox(
        "Select Tool",
        ["Data Cleaning", "Data Merge"]
    )

    # -----------------------------
    # DATA CLEANING
    # -----------------------------
    if tool == "Data Cleaning":

        file = st.file_uploader("Upload Dataset", type=["csv", "xlsx", "json"])

        if file:
            df = read_file(file)

            if df is not None:
                st.subheader("Raw Data Preview")
                st.dataframe(df.head())

                if st.button("Run Cleaning Pipeline"):
                    cleaned_df, report = run_cleaning_pipeline(df)

                    st.success("Data Cleaning Completed!")

                    st.subheader("Cleaned Data")
                    st.dataframe(cleaned_df.head())

                    st.subheader("Cleaning Report")

                    col1, col2 = st.columns(2)
                    col1.metric("Rows Removed", report["rows_before"] - report["rows_after"])
                    col1.metric("Duplicates Removed", report["duplicates_removed"])
                    col2.metric("Columns Removed", report["cols_before"] - report["cols_after"])
                    col2.metric("Spaces Trimmed", report["spaces_trimmed"])

                    if report["numeric_converted"]:
                        st.info(f"Converted to Numeric: {report['numeric_converted']}")

                    download_file(cleaned_df, "cleaned_data")

    # -----------------------------
    # DATA MERGE
    # -----------------------------
    elif tool == "Data Merge":

        file1 = st.file_uploader("Upload First File", type=["csv", "xlsx", "json"])
        file2 = st.file_uploader("Upload Second File", type=["csv", "xlsx", "json"])

        if file1 and file2:
            df1 = clean_column_names(read_file(file1))
            df2 = clean_column_names(read_file(file2))

            common_cols = list(df1.columns.intersection(df2.columns))

            if not common_cols:
                st.error("No common columns found.")
                return

            column = st.selectbox("Select Column to Merge On", common_cols)
            merge_type = st.selectbox("Select Merge Type", ["inner", "outer", "left", "right"])

            if st.button("Merge Now"):
                merged_df = perform_merge(df1, df2, column, merge_type)

                st.success("Merge Completed!")
                st.dataframe(merged_df.head())

                download_file(merged_df, "merged_data")


if __name__ == "__main__":
    main()
