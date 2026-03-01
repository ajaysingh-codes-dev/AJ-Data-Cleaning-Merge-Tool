import pandas as pd
import streamlit as st
from io import BytesIO
import numpy as np


report = {
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

def read_file(file):
    try:
        file_Ex = {"csv":pd.read_csv,
                "json":pd.read_json,
                "xlsx":pd.read_excel,
                "xls":pd.read_excel,}
        
        filename = file.name.split(".")[-1].lower()
        if filename in file_Ex:
            return file_Ex[filename](file)
        else:
            st.error(f"Unexpected file extension: .{filename}")
            return None
    except Exception as e:
        st.error(f"file reading error, {e}")
        return None
    
def clean_column(df1):
    df1.columns = df1.columns.str.strip().str.title().str.replace(" ","_", regex=True)
    return df1

def get_common_column(df1, df2):
    comman_col = list(df1.columns.intersection(df2.columns))

    if len(comman_col) == 0:
        st.error("No common columns found. Cannot merge!")
        st.stop()
    else:
        return comman_col
    
def perform_merge(df1, df2, on_column, merge_type):
    st.success("🚀 Data merge Completed Successfully!")
    return pd.merge(df1, df2, on=on_column, how=merge_type)
    
def remove_empty_rows_columns(df):
    row_before, col_before = df.shape

    df = df.dropna( how="all")
    df = df.dropna(axis=1, how="all")

    row_after, col_after = df.shape

    report["empty_rows_removed"] = row_before - row_after
    report["empty_cols_removed"] = col_before - col_after

    return df

def remove_duplicates(df):
    row_before = len(df)
    df = df.drop_duplicates()
    row_after = len(df)
    remove = row_before - row_after
    report["duplicates_removed"] = row_before - row_after
    return df

def trim_string_spaces(df):
    extra_spaces = 0
    object_col = df.select_dtypes(include="object").columns
    for col in object_col:
        before = df[col].copy()
        df[col] =  df[col].str.strip()
        extra_spaces += ((before != df[col]) & before.notna()).sum()

    report["spaces_trimmed"] = extra_spaces
    return df

def clean_numeric_strings(df):
    object_cols = df.select_dtypes(include="object").columns
    
    for col in object_cols:
        cleaned_series = (
            df[col]
            .astype(str)
            .str.replace(r"[,$₹% ]", "", regex=True)
            .replace(['nan', 'None', ''], pd.NA)
        )
        
        converted = pd.to_numeric(cleaned_series, errors="coerce")
        
        # Only replace column if conversion actually worked for most values
        if converted.notna().sum() > 0:
    df[col] = converted
    
    return df
def save_cleaned_df(df):
    option = st.radio("Choose file format for cleaned file:", 
                      ("csv", "excel", "json"), key="clean_download")

    if option == "csv":
        data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Cleaned CSV",
                           data,
                           "cleaned_data.csv",
                           "text/csv")

    elif option == "excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Download Cleaned Excel",
                           output.getvalue(),
                           "cleaned_data.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif option == "json":
        data = df.to_json(orient="records", indent=4).encode("utf-8")
        st.download_button("Download Cleaned JSON",
                           data,
                           "cleaned_data.json",
                           "application/json")

def save_df(df):
    option = st.radio("Choose file format:", ("csv", "excel", "json"))

    if option == "csv":
        data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data, "merged.csv", "text/csv")

    elif option == "excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            "Download Excel",
            output.getvalue(),
            "merged.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif option == "json":
        data = df.to_json(orient="records", indent=4).encode("utf-8")
        st.download_button("Download JSON", data, "merged.json", "application/json")

def main():
    st.set_page_config(page_title="AJ_Tech_Tool", layout="wide")

    st.title("AJ – Intelligent Data Cleaning & Merge Tool")

    st.markdown("""
    Automatically clean, standardize, and transform raw data into analysis-ready datasets  
    with detailed cleaning reports.
    """)

    with st.sidebar:
        st.header("Select Tool")
        tool = st.selectbox(
    "Choose Operation",
    ["Welcome Dashboard", "Data Cleaning", "Data Merge"]
)
    if tool == "Welcome Dashboard":

        st.markdown("""
            <h1 style='text-align: center;'>🚀 Welcome to AJ – Tech Tool</h1>
            <p style='text-align: center; color: gray; font-size:18px;'>
            Intelligent Data Cleaning & Merge System
            </p>
            <hr>
        """, unsafe_allow_html=True)

        st.subheader("📌 What This Tool Can Do")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### 🧹 Data Cleaning Engine
            - Remove empty rows & columns  
            - Trim extra spaces  
            - Remove duplicates  
            - Smart numeric conversion  
            - Generate cleaning report  
            """)

        with col2:
            st.markdown("""
            ### 🔗 Data Merge Engine
            - Detect common columns  
            - Merge with inner / outer / left / right  
            - Preview before export  
            - Download final dataset  
            """)

        st.divider()

        st.subheader("⚡ How To Use")

        st.markdown("""
        1️⃣ Select a tool from the sidebar  
        2️⃣ Upload your dataset(s)  
        3️⃣ Review preview  
        4️⃣ Download cleaned or merged file  
        """)

        st.success("Ready to optimize your data? Select a tool from the sidebar 👈")

    # Tool Routing
    elif tool == "Data Cleaning":

        st.markdown("""
            <h2 style='text-align: center;'>
                ⚡ AJ – Tech Data Cleaning Engine
            </h2>
            <p style='text-align: center; color: gray;'>
                Upload → Clean → Optimize → Download
            </p>
            <hr>
        """, unsafe_allow_html=True)

        file = st.file_uploader("📂 Upload your dataset",
                                type=["csv", "xlsx", "json"],
                                help="Supported formats: CSV, Excel, JSON")

        if file:
            with st.spinner("🔍 Reading file..."):
                df = read_file(file)

            st.success("✅ File Loaded Successfully")

            # BEFORE CLEANING SECTION
            with st.expander("📊 View Raw Data", expanded=False):
                st.dataframe(df, use_container_width=True)

            # Metrics before cleaning
            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", df.shape[0])
            col2.metric("Columns", df.shape[1])
            col3.metric("Missing Values", df.isna().sum().sum())

            st.markdown("---")
            st.markdown("### 🧹 Running Cleaning Pipeline...")

            progress = st.progress(0)

            report["rows_before"] = df.shape[0]
            report["cols_before"] = df.shape[1]

            df = clean_column(df)
            progress.progress(20)

            df = trim_string_spaces(df)
            progress.progress(40)

            df = remove_duplicates(df)
            progress.progress(60)

            df = clean_numeric_strings(df)
            progress.progress(80)

            df = remove_empty_rows_columns(df)
            progress.progress(100)

            st.success("🚀 Data Cleaning Completed Successfully!")

            report["rows_after"] = df.shape[0]
            report["cols_after"] = df.shape[1]

            # AFTER CLEANING SECTION
            st.markdown("### ✨ Cleaned Dataset")

            col1, col2, col3 = st.columns(3)
            col1.metric("Rows After Cleaning", df.shape[0])
            col2.metric("Columns After Cleaning", df.shape[1])
            col3.metric("Remaining Missing", df.isna().sum().sum())

            with st.expander("🔎 View Cleaned Data", expanded=True):
                st.dataframe(df, use_container_width=True)

            st.subheader("📋 Cleaning Report")

            col1, col2 = st.columns(2)

            col1.metric("Rows Removed", report["rows_before"] - report["rows_after"])
            col1.metric("Duplicates Removed", report["duplicates_removed"])

            col2.metric("Columns Removed", report["cols_before"] - report["cols_after"])
            col2.metric("Spaces Trimmed", report["spaces_trimmed"])

            st.markdown("---")

            # Download button
            st.subheader(
                "⬇ Download Cleaned File",)
            save_cleaned_df(df)

        # call cleaning functions here

    elif tool == "Data Merge":
        st.markdown("""
            <h2 style='text-align: center;'>
                ⚡ AJ – Tech Data Merge Engine
            </h2>
            <p style='text-align: center; color: gray;'>
                Upload → Custome → Merge → Download
            </p>
            <hr>
        """, unsafe_allow_html=True)
        st.spinner("Reading files...")
        file1 = st.file_uploader("First file", type=["csv", "json", "xlsx"],help="Supported formats: CSV, Excel, JSON")
        file2 = st.file_uploader("Second file", type=["csv", "json", "xlsx"],help="Supported formats: CSV, Excel, JSON")

        if file1 and file2:
            df1 = clean_column(read_file(file1))
            df2 = clean_column(read_file(file2))

            tab1, tab2 = st.tabs(["📄 File 1 Preview", "📄 File 2 Preview"])
            with tab1:
                st.subheader("Your File_1 Data Before Mergeing Preview")
                st.dataframe(df1.head())
            with tab2:
                st.subheader("Your File_2 Data Before Mergeing Preview")
                st.dataframe(df2.head())
            
            common_col = get_common_column(df1, df2)

            col1, col2 = st.columns(2)
            with col1:
                on_column = st.selectbox("Avaliable column to merge on", common_col)
            with col2:
                merge_type = st.selectbox("Select Merge type",["inner", "outer", "left", "right"])
            
            st.divider()
            merged_df = perform_merge(df1, df2, on_column, merge_type)
            
            st.subheader("Merged Data Preview")
            st.write(f"Shape: {merged_df.shape[0]} rows, {merged_df.shape[1]} columns")
            st.dataframe(merged_df.head(10), use_container_width=True)

            st.subheader("Export Result")
            save_df(merged_df)
        # call merge logic here


main()
