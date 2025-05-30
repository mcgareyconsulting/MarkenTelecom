import pandas as pd
import os


def read_district_violation_codes(excel_path: str = "district_violation_codes.xlsx"):
    """
    Reads the district_violation_codes.xlsx file and returns a DataFrame.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"{excel_path} not found.")
    df = pd.read_excel(excel_path)
    return df


def get_violation_titles_for_district(
    district: str, excel_path: str = "district_violation_codes.xlsx"
):
    """
    Returns a list of violation titles for the given district.
    """
    df = read_district_violation_codes(excel_path)
    # Assuming columns are named 'District' and 'Title'
    titles = df[df["District"] == district]["Title"].dropna().unique().tolist()
    return titles
