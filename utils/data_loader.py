import pandas as pd
import glob
import io

# --- Authenticate with Google Drive ---
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import streamlit as st
import os

def get_drive():
    gauth = GoogleAuth()

    # Extract secrets safely from st.secrets
    service_info = st.secrets["google_service_account"]

    # Write it to a temporary JSON file
    import json, os
    with open("service_secrets.json", "w") as f:
        json.dump(dict(service_info), f)  # <--- convert to regular dict first!

    gauth.DEFAULT_SETTINGS['client_config_backend'] = 'service'
    gauth.DEFAULT_SETTINGS['service_config'] = {
        'client_json_file_path': 'service_secrets.json'
    }

    gauth.ServiceAuth()
    return GoogleDrive(gauth)

drive = get_drive()
FOLDER_ID = "16UY4IslY4KFTo5O1I6MBMzuPF9IQGwuE"  # <-- Replace this with your actual Drive folder ID

def load_drive_csvs_by_prefix(prefix):
    file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
    matching_files = [f for f in file_list if f['title'].startswith(prefix) and f['title'].endswith(".csv")]

    if not matching_files:
        print(f"[WARNING] No files found with prefix '{prefix}'")
        return pd.DataFrame()

    df_list = []
    for file in matching_files:
        try:
            content = file.GetContentString()
            df = pd.read_csv(io.StringIO(content))
            df_list.append(df)
        except Exception as e:
            print(f"[ERROR] Failed to load {file['title']}: {e}")

    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)
        merged_df.drop_duplicates(inplace=True)
        return merged_df
    else:
        return pd.DataFrame()


# Wrapper functions
def load_daily_availability_regional(): return load_drive_csvs_by_prefix("daily_regional")
def load_daily_availability_nop(): return load_drive_csvs_by_prefix("daily_nop")

def load_kpi_data(sheet_name="KPI_Data"):
    try:
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
        target_file = next((f for f in file_list if f['title'].lower() == 'kpi_data.xlsx'), None)

        if not target_file:
            print("[ERROR] kpi_data.xlsx not found in Drive folder.")
            return pd.DataFrame()

        file_content = target_file.GetContentFile('kpi_data.xlsx')
        df = pd.read_excel("kpi_data.xlsx", sheet_name=sheet_name, engine="openpyxl")

        #print("[DEBUG] Columns loaded:", df.columns.tolist())

        return df

    except Exception as e:
        print(f"[ERROR] Failed to load KPI data from Drive: {e}")
        return pd.DataFrame()


# --- Load Ticketing Data from Google Drive ---
def load_ticketing_data():
    daily_frames = []
    mtd_frames = []

    file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
    ticketing_files = [f for f in file_list if f['title'].startswith("ticketing") and f['title'].endswith(".xlsx")]

    for file in ticketing_files:
        try:
            filename = file['title']
            file.GetContentFile(filename)

            daily_df = pd.read_excel(filename, sheet_name="Daily", engine="openpyxl")
            mtd_df = pd.read_excel(filename, sheet_name="MTD", engine="openpyxl")

            for df in [daily_df, mtd_df]:
                df["Date"] = pd.to_datetime(df["Date"])
                df["Month"] = df["Date"].dt.strftime("%B")
                df["Year"] = df["Date"].dt.year

            daily_frames.append(daily_df)
            mtd_frames.append(mtd_df)

            os.remove(filename)  # Clean up local file

        except Exception as e:
            print(f"[ERROR] Failed to read {file['title']}: {e}")

    df_daily = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()
    df_mtd = pd.concat(mtd_frames, ignore_index=True) if mtd_frames else pd.DataFrame()

    return df_daily, df_mtd


# --- Load Availability Data from Google Drive ---
def load_availability_regional_data():
    return load_drive_csvs_by_prefix("monthly_regional")

def load_availability_nop_data():
    return load_drive_csvs_by_prefix("monthly_nop")

def load_availability_site_data():
    return load_drive_csvs_by_prefix("monthly_site")
