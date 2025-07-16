import streamlit as st
import pandas as pd
import io
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# --- Authenticate with Google Drive ---
def get_drive():
    service_info = dict(st.secrets["google_service_account"])
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_info, scopes)

    gauth = GoogleAuth()
    gauth.credentials = credentials
    gauth.Authorize()

    return GoogleDrive(gauth)

FOLDER_ID = "16UY4IslY4KFTo5O1I6MBMzuPF9IQGwuE"  # <-- Replace with your actual folder ID


# --- Load CSV files by prefix ---
def load_drive_csvs_by_prefix(prefix):
    drive = get_drive()
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


# --- Load KPI Excel file from Google Drive ---
@st.cache_data(ttl=3600)
def load_kpi_data(sheet_name="KPI_Data"):
    try:
        drive = get_drive()
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
        target_file = next((f for f in file_list if f['title'].lower() == 'kpi_data.xlsx'), None)

        if not target_file:
            print("[ERROR] kpi_data.xlsx not found in Drive folder.")
            return pd.DataFrame()

        filename = "kpi_data.xlsx"
        target_file.GetContentFile(filename)

        df = pd.read_excel(filename, sheet_name=sheet_name, engine="openpyxl")
        os.remove(filename)
        return df

    except Exception as e:
        print(f"[ERROR] Failed to load KPI data from Drive: {e}")
        return pd.DataFrame()


# --- Load Ticketing Data from Google Drive ---
@st.cache_data(ttl=3600)
def load_ticketing_data():
    drive = get_drive()
    daily_frames = []
    mtd_frames = []
    daily_cluster_frames = []
    mtd_cluster_frames = []

    file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
    ticketing_files = [f for f in file_list if f['title'].startswith("ticketing") and f['title'].endswith(".xlsx")]

    for file in ticketing_files:
        try:
            filename = file['title']
            file.GetContentFile(filename)

            all_sheets = pd.read_excel(filename,
                                       sheet_name=["Daily", "MTD", "Daily_Cluster", "MTD_Cluster"],
                                       engine="openpyxl")

            daily_df = all_sheets.get("Daily", pd.DataFrame())
            mtd_df = all_sheets.get("MTD", pd.DataFrame())
            daily_cluster_df = all_sheets.get("Daily_Cluster", pd.DataFrame())
            mtd_cluster_df = all_sheets.get("MTD_Cluster", pd.DataFrame())

            for df in [daily_df, mtd_df, daily_cluster_df, mtd_cluster_df]:
                if not df.empty and "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                    df["Month"] = df["Date"].dt.strftime("%B")
                    df["Year"] = df["Date"].dt.year

            if not daily_df.empty:
                daily_frames.append(daily_df)
            if not mtd_df.empty:
                mtd_frames.append(mtd_df)
            if not daily_cluster_df.empty:
                daily_cluster_frames.append(daily_cluster_df)
            if not mtd_cluster_df.empty:
                mtd_cluster_frames.append(mtd_cluster_df)

            os.remove(filename)

        except Exception as e:
            print(f"[ERROR] Failed to load {file['title']}: {e}")

    df_daily = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()
    df_mtd = pd.concat(mtd_frames, ignore_index=True) if mtd_frames else pd.DataFrame()
    df_daily_cluster = pd.concat(daily_cluster_frames, ignore_index=True) if daily_cluster_frames else pd.DataFrame()
    df_mtd_cluster = pd.concat(mtd_cluster_frames, ignore_index=True) if mtd_cluster_frames else pd.DataFrame()

    return df_daily, df_mtd, df_daily_cluster, df_mtd_cluster


# --- Load Worst Site Tracker from Google Drive ---
@st.cache_data(ttl=3600)
def load_worst_site_data():
    try:
        drive = get_drive()
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
        target_file = next((f for f in file_list if f['title'].lower() == 'worst_site.xlsx'), None)

        if not target_file:
            print("[ERROR] worst_site.xlsx not found in Drive folder.")
            return pd.DataFrame()

        filename = "worst_site.xlsx"
        target_file.GetContentFile(filename)

        df = pd.read_excel(filename, sheet_name="Tracking Red Zone", engine="openpyxl", header=1)
        os.remove(filename)
        return df

    except Exception as e:
        print(f"[ERROR] Failed to load worst site data from Drive: {e}")
        return pd.DataFrame()


# --- Wrapper functions for Daily Availability ---
@st.cache_data(ttl=3600)
def load_daily_availability_regional():
    return load_drive_csvs_by_prefix("daily_regional")

@st.cache_data(ttl=3600)
def load_daily_availability_nop():
    return load_drive_csvs_by_prefix("daily_nop")

@st.cache_data(ttl=3600)
def load_daily_availability_site():
    return load_drive_csvs_by_prefix("daily_site")


# --- Wrapper functions for Monthly Availability ---
@st.cache_data(ttl=3600)
def load_availability_regional_data():
    return load_drive_csvs_by_prefix("monthly_regional")

@st.cache_data(ttl=3600)
def load_availability_nop_data():
    return load_drive_csvs_by_prefix("monthly_nop")

@st.cache_data(ttl=3600)
def load_availability_site_data():
    return load_drive_csvs_by_prefix("monthly_site")

@st.cache_data(ttl=3600)
def load_resource_data(sheet_name="Rekap Tiket"):
    try:
        drive = get_drive()
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
        resource_files = [f for f in file_list if f['title'].lower().startswith('resource') and f['title'].endswith('.xlsx')]

        if not resource_files:
            print("[WARNING] No resource*.xlsx files found in Drive folder.")
            return pd.DataFrame()

        df_list = []
        for file in resource_files:
            try:
                filename = file['title']
                file.GetContentFile(filename)

                df = pd.read_excel(filename, sheet_name=sheet_name, engine="openpyxl")

                df.columns = (
                    df.columns
                    .str.replace(r"\xa0", " ", regex=True)
                    .str.replace(r"[–‐‑−]", "-", regex=True)
                    .str.strip()
                )

                df['Source File'] = filename
                df_list.append(df)
                os.remove(filename)
            except Exception as e:
                print(f"[ERROR] Failed to load {file['title']} ({sheet_name}): {e}")

        if df_list:
            combined_df = pd.concat(df_list, ignore_index=True)
            combined_df.drop_duplicates(inplace=True)
            return combined_df
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"[ERROR] Failed to load resource data ({sheet_name}): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_ticketing_overview_data():
    severity_frames = []
    rc_cat_frames = []
    ticket_frames = []
    dpg_frames = []

    try:
        drive = get_drive()
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
        overview_files = [f for f in file_list if f['title'].startswith("overview") and f['title'].endswith(".xlsx")]

        if not overview_files:
            print("[WARNING] No 'overview*.xlsx' files found.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        for file in overview_files:
            try:
                filename = file['title']
                file.GetContentFile(filename)

                all_sheets = pd.read_excel(filename, sheet_name=["Severity", "RC_Cat", "Ticket", "DPG"], engine="openpyxl")

                df_sev = all_sheets.get("Severity", pd.DataFrame())
                df_rc = all_sheets.get("RC_Cat", pd.DataFrame())
                df_tk = all_sheets.get("Ticket", pd.DataFrame())
                df_dpg = all_sheets.get("DPG", pd.DataFrame())

                for df in [df_sev, df_rc, df_tk, df_dpg]:
                    if not df.empty:
                        df.columns = df.columns.str.strip()
                        df["Source File"] = filename

                if not df_sev.empty and "Date" in df_sev.columns:
                    df_sev["Date"] = pd.to_datetime(df_sev["Date"], errors="coerce")
                    if "Month" not in df_sev.columns:
                        df_sev["Month"] = df_sev["Date"].dt.month
                    if "Year" not in df_sev.columns:
                        df_sev["Year"] = df_sev["Date"].dt.year

                if not df_sev.empty:
                    severity_frames.append(df_sev)
                if not df_rc.empty:
                    rc_cat_frames.append(df_rc)
                if not df_tk.empty:
                    ticket_frames.append(df_tk)
                if not df_dpg.empty:
                    dpg_frames.append(df_dpg)

                os.remove(filename)

            except Exception as e:
                print(f"[ERROR] Failed to process {file['title']}: {e}")

        df_severity = pd.concat(severity_frames, ignore_index=True) if severity_frames else pd.DataFrame()
        df_rc_cat = pd.concat(rc_cat_frames, ignore_index=True) if rc_cat_frames else pd.DataFrame()
        df_ticket = pd.concat(ticket_frames, ignore_index=True) if ticket_frames else pd.DataFrame()
        df_dpg = pd.concat(dpg_frames, ignore_index=True) if dpg_frames else pd.DataFrame()

        return df_severity, df_rc_cat, df_ticket, df_dpg

    except Exception as e:
        print(f"[ERROR] load_ticketing_overview_data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
