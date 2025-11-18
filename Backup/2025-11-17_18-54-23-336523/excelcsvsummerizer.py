import pandas as pd
import os
from pathlib import Path
from datetime import datetime

def detect_file(folder_path: str):
    """
    Detects whether the provided file is CSV or Excel.
    If CSV -> converts it to Excel and reloads the Excel version (Logic A).
    If Excel -> loads it directly.

    Parameters:
        file_path (str): Path to the input CSV or Excel file.

    Returns:
        pd.DataFrame: A DataFrame loaded from an Excel file.
    """
    try:
        if folder_path.endswith(".csv"):
            csv_df = pd.read_csv(folder_path)
            
            original_filepath = Path(folder_path)
            excel_df = original_filepath.parent / f"{original_filepath.stem}_converted.xlsx"

            csv_df.to_excel(excel_df, index=False)

            excel_df = pd.read_excel(excel_df)
            return excel_df
        
        elif folder_path.endswith(".xlsx"):
            excel_df = pd.read_excel(folder_path)
            return excel_df
        else:
            raise ValueError("Unsupported file type. Only .csv or .xlsx allowed.")
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def process_file_generate_report(df: pd.DataFrame, destination_path: str):
    """
    Processes a standardized DataFrame (Excel-based) and generates a summary report
    containing aggregates for all numeric columns.

    Parameters:
        df (pd.DataFrame): Loaded DataFrame (must originate from Excel under Logic A).
        destination_path (str): Directory where the summary Excel will be saved.

    Returns:
        None
    """
    if df is None:
        print("[iNFO] no data to process.")
        return
    
    df.columns = df.columns.str.strip()
    numeric_cols = df.select_dtypes(include="number").columns

    summary_data = []

    for col in numeric_cols:
        summary_data.append({
            "Column": col,
            "Sum": df[col].sum(),
            "Average": df[col].mean(),
            "Min": df[col].min(),
            "Max": df[col].max(),
            "Count":df[col].count()
        })  
    
    summary_df = pd.DataFrame(summary_data)

    os.makedirs(destination_path, exist_ok=True)

    timestamp = f"summary_{datetime.today().strftime("%d-%m-%Y_%H-%M-%S")}.xlsx"
    file_name_destination = os.path.join(destination_path, timestamp)
    summary_df.to_excel(file_name_destination, index=False)

    
if __name__ == "__main__":

    source_file  = "Newprojects/AutomationScripting/testforexcelcsv.csv"
    destination = "Newprojects/AutomationScripting"
    df = detect_file(source_file )
    process_file_generate_report(df, destination)

