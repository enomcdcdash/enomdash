import pandas as pd
import glob
import os

# --- Load KPI Data ---
def load_kpi_data(sheet_name="KPI_Data"):
    try:
        return pd.read_excel("data/kpi_data.xlsx", sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"[ERROR] Failed to load KPI data: {e}")
        return pd.DataFrame()

# --- Load Ticketing Data ---
def load_ticketing_data(data_folder="data"):
    daily_frames = []
    mtd_frames = []

    files = glob.glob(os.path.join(data_folder, "ticketing*.xlsx"))

    for file in files:
        try:
            daily_df = pd.read_excel(file, sheet_name="Daily", engine="openpyxl")
            mtd_df = pd.read_excel(file, sheet_name="MTD", engine="openpyxl")

            for df in [daily_df, mtd_df]:
                df["Date"] = pd.to_datetime(df["Date"])
                df["Month"] = df["Date"].dt.strftime("%B")
                df["Year"] = df["Date"].dt.year

            daily_frames.append(daily_df)
            mtd_frames.append(mtd_df)

        except Exception as e:
            print(f"[ERROR] Failed to read {file}: {e}")

    df_daily = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()
    df_mtd = pd.concat(mtd_frames, ignore_index=True) if mtd_frames else pd.DataFrame()

    return df_daily, df_mtd

# --- Load Availability Data ---
def load_availability_regional_data():
    try:
        return pd.read_csv("data/monthly_regional.csv")
    except Exception as e:
        print(f"[ERROR] Failed to read regional availability data: {e}")
        return pd.DataFrame()

def load_availability_nop_data():
    try:
        return pd.read_csv("data/monthly_nop.csv")
    except Exception as e:
        print(f"[ERROR] Failed to read NOP availability data: {e}")
        return pd.DataFrame()

def load_availability_site_data():
    try:
        return pd.read_csv("data/monthly_site.csv")
    except Exception as e:
        print(f"[ERROR] Failed to read Site availability data: {e}")
        return pd.DataFrame()
