import pandas as pd

# --- helpers.py ---
def summarize_availability_nop(df):
    df_summary = (
        df.groupby(["Month", "area", "regional", "networksite", "site_class"], as_index=False)
        .agg({"Availability (Ave)": "mean"})
        .rename(columns={"Availability (Ave)": "Availability"})
        .sort_values(by=["Month", "area", "regional", "networksite", "site_class"])
    )
    return df_summary

def summarize_availability_regional(df):
    df_summary = (
        df.groupby(["Month", "area", "regional", "site_class"], as_index=False)
        .agg({"Availability (Ave)": "mean"})
        .rename(columns={"Availability (Ave)": "Availability"})
        .sort_values(by=["Month", "area", "regional", "site_class"])
    )
    return df_summary

def summarize_availability_area(df):
    df_summary = (
        df.groupby(["Month", "area", "site_class"], as_index=False)
        .agg({"Availability (Ave)": "mean"})
        .rename(columns={"Availability (Ave)": "Availability"})
        .sort_values(by=["Month", "area", "site_class"])
    )
    return df_summary

def summarize_achievement_nop(df):
    df["Achieved"] = df["Availability (Ave)"] >= df["target (%)"]
    df_summary = (
        df.groupby(["Month", "area", "regional", "networksite"], as_index=False)
        .agg(
            Achievement=("Achieved", "mean"),
            Achieved_Count=("Achieved", lambda x: (x == True).sum()),
            Not_Achieved_Count=("Achieved", lambda x: (x == False).sum())
        )
    )
    return df_summary

def summarize_achievement_regional(df):
    df["Achieved"] = df["Availability (Ave)"] >= df["target (%)"]
    
    df_summary = (
        df.groupby(["Month", "area", "regional"], as_index=False)
        .agg(
            Achievement=("Achieved", "mean"),
            Achieved_Count=("Achieved", lambda x: (x == True).sum()),
            Not_Achieved_Count=("Achieved", lambda x: (x == False).sum())
        )
    )
    
    return df_summary

def summarize_achievement_area(df):
    df["Achieved"] = df["Availability (Ave)"] >= df["target (%)"]
    
    df_summary = (
        df.groupby(["Month", "area"], as_index=False)
        .agg(
            Achievement=("Achieved", "mean"),
            Achieved_Count=("Achieved", lambda x: (x == True).sum()),
            Not_Achieved_Count=("Achieved", lambda x: (x == False).sum())
        )
    )
    
    return df_summary

def summarize_availability_overall(df):
    df_summary = (
        df.groupby(["Month", "site_class"], as_index=False)
        .agg({"Availability (Ave)": "mean"})
        .rename(columns={"Availability (Ave)": "Availability"})
        .sort_values(by=["Month", "site_class"])
    )
    return df_summary

def summarize_achievement_overall(df):
    df["Achieved"] = df["Availability (Ave)"] >= df["target (%)"]
    df_summary = (
        df.groupby(["Month"], as_index=False)
        .agg(
            Achievement=("Achieved", "mean"),
            Achieved_Count=("Achieved", lambda x: (x == True).sum()),
            Not_Achieved_Count=("Achieved", lambda x: (x == False).sum())
        )
    )
    return df_summary

def clean_worst_site_data(df):
    if df.empty:
        return df

    df.columns = df.columns.str.strip()  # Optional, just in case
    df = df.dropna(subset=["Site ID"])
    return df

def get_pie_chart_data(df, group_by_col):
    if df.empty or group_by_col not in df.columns:
        return pd.DataFrame()

    summary = (
        df.groupby(group_by_col)["Site ID"]
        .nunique()
        .reset_index(name="Site Count")
        .sort_values("Site Count", ascending=False)
    )
    return summary
