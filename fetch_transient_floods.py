import sys
import requests
import pandas as pd

ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

def fetch_empty_cases(limit: int = 10000, max_hours: float = 12.0, min_hours: float = 0.25):
    print("Connecting to NYC 311 SODA API...")

    # Focus directly on stormwater ponding and catch basin overflow
    params = {
        "$select": (
            "unique_key, created_date, closed_date, complaint_type, descriptor, "
            "incident_address, street_name, cross_street_1, cross_street_2, "
            "borough, incident_zip, latitude, longitude, resolution_description"
        ),
        "$where": """
            agency = 'DEP'
            AND complaint_type = 'Sewer'
            AND descriptor IN ('Street Flooding (SJ)', 'Catch Basin Clogged/Flooding (SC)')
            AND closed_date IS NOT NULL
            AND resolution_description IS NOT NULL
        """,
        "$order": "created_date DESC",
        "$limit": limit
    }

    try:
        res = requests.get(ENDPOINT, params=params, timeout=60)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return pd.DataFrame()

    raw_data = res.json()
    if not raw_data:
        print("No raw records returned from API.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)
    print(f"Retrieved {len(df)} total closed street/catch basin flooding tickets.")

    # Target the exact dispositions identified by DEP inspection
    patterns = {
        "Naturally Receded (Could Not Find)": r"could not find the problem",
        "Hydraulic Surcharge (Rain Intensity)": r"surcharge conditions have been confirmed"
    }

    # Combined regex to match either self-resolving case
    combined_regex = r"could not find the problem|surcharge conditions have been confirmed"
    match_mask = df["resolution_description"].str.contains(combined_regex, case=False, na=False, regex=True)
    
    # match_mask = df["resolution_description"].str.contains(combined_regex, case=False, na=False)
    filtered_df = df[match_mask].copy()

    if filtered_df.empty:
        print("No records matched the target resolution descriptions.")
        return pd.DataFrame()

    # Label resolution category
    def categorize(text):
        text_lower = str(text).lower()
        if "could not find the problem" in text_lower:
            return "Naturally Receded (Unobserved)"
        elif "surcharge conditions" in text_lower:
            return "Hydraulic Capacity Surcharge"
        return "Other"

    filtered_df["drain_category"] = filtered_df["resolution_description"].apply(categorize)

    # Convert timestamps and compute delta t (duration in decimal hours)
    filtered_df["created_date"] = pd.to_datetime(filtered_df["created_date"])
    filtered_df["closed_date"] = pd.to_datetime(filtered_df["closed_date"])
    filtered_df["duration_hours"] = (
        (filtered_df["closed_date"] - filtered_df["created_date"]).dt.total_seconds() / 3600.0
    )

    # Filter out anomalous durations: keep tickets inspected within 15 min to 12 hours
    transient_df = filtered_df[
        (filtered_df["duration_hours"] >= min_hours) & 
        (filtered_df["duration_hours"] <= max_hours)
    ].copy()

    transient_df.sort_values(by="created_date", ascending=False, inplace=True)
    return transient_df

def main():
    df = fetch_empty_cases(limit=10000, max_hours=12.0, min_hours=0.25)

    if df.empty:
        print("No transient cases met the time window criteria.")
        return

    print("\n--- Summary: Transient Flooding (Self-Resolved / Capacity Exceeded) ---")
    print(f"Total matching cases:       {len(df)}")
    print(f"Median response/clear time: {df['duration_hours'].median():.2f} hours")
    print(f"Mean response/clear time:   {df['duration_hours'].mean():.2f} hours")

    print("\nBreakdown by Drain Category:")
    print(df["drain_category"].value_counts().to_string())

    print("\nBreakdown by Borough:")
    print(df["borough"].value_counts().to_string())

    output_filename = "nyc_311_self_resolved_floods.csv"
    df.to_csv(output_filename, index=False)
    print(f"\nSaved {len(df)} validated records to '{output_filename}'")

if __name__ == "__main__":
    main()