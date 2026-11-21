"""Week 8: fetch country COVID-19 records and save them as DATA/raw.csv.

Mohammed Mohammed Alhaji
Data Science | CST1510
Run with: python fetch_data.py
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import requests


URL = "https://disease.sh/v3/covid-19/countries"
PARAMS = {}
RECORDS_KEY = None

RENAME = {}
KEEP = [
    "country",
    "continent",
    "cases",
    "deaths",
    "recovered",
    "tests",
    "population",
    "active",
]
MUST_HAVE = ["cases", "continent"]
RAW_FILE = Path(__file__).parent / "DATA" / "raw.csv"


def get_data(url, params):
    """Return the API's JSON data, or None when the request fails."""
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        print("Could not get the data:", error)
        return None


def make_table(data, records_key):
    """Convert the list of JSON records into a flat table."""
    records = data[records_key] if records_key else data
    return pd.json_normalize(records, sep="_")


def tidy_data(df):
    """Keep the chosen columns and remove records missing required values."""
    df = df.rename(columns=RENAME)
    df = df[KEEP].copy()
    for column in ["country", "continent"]:
        df[column] = df[column].str.strip().replace("", pd.NA)
    return df.dropna(subset=MUST_HAVE)


def save_data(df, path):
    """Save the CSV, replacing the old file only after writing succeeds."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            df.to_csv(temporary_file, index=False)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    print(f"Saved {len(df)} rows to {path}")


if __name__ == "__main__":
    data = get_data(URL, PARAMS)
    if data is not None:
        try:
            table = make_table(data, RECORDS_KEY)
            table = tidy_data(table)
            if len(table) < 50:
                raise ValueError("The dataset needs at least 50 usable records.")
            save_data(table, RAW_FILE)
            print(table.head())
        except (KeyError, TypeError, ValueError, OSError) as error:
            print("Could not save the data:", error)
