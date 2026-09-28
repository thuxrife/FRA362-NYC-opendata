import io
import re
import sys
import requests
import pandas as pd

API_ENDPOINT = "https://publicapi.traffy.in.th/teamchadchart-stat-api/download/bangkok_monthly"

# Default API registration credentials for academic research
DEFAULT_PARAMS = {
    "name": "KMUTT_Student_Research",
    "org": "KMUTT_FRA362",
    "email": "student@kmutt.ac.th",
    "purpose": "Academic_research_transient_urban_floods"
}

# Method A Regex Patterns
PATTERNS = {
    "chronic_clog": r"ไขมัน|ขยะอุดตัน|ลอกท่อ|ทุก\s*\d+\s*เดือน|เป็นประจำ|ตันสะสม|เรื้อรัง|มากกว่า\s*1\s*สัปดาห์|นานแล้ว|ตะไคร่|ไม่มีท่อ",
    "structural_defect": r"ฝาท่อแตก|ฝาท่อชำรุด|ท่อทรุด|ท่อแตก|เหล็กยื่น|พัง|เป็นหลุม|ฝาท่อพัง",
    "hydraulic_surcharge": r"ระบายไม่ทัน|น้ำรอระบาย|ฝนตกหนัก|ขังช่วงฝน|เวลาฝนตก|ระบายช้า|ฝนตกน้ำท่วม|ขณะฝนตก",
    "naturally_receded": r"น้ำแห้งแล้ว|ลดลงแล้ว|แห้งเป็นปกติ|ไม่พบปัญหาน้ำท่วม|น้ำแห้ง|น้ำลด"
}

def classify_bangkok_text(text: str, problem_type: str = "") -> str:
    full_text = f"{text or ''} {problem_type or ''}".lower()
    if re.search(PATTERNS["chronic_clog"], full_text):
        return "Chronic Infrastructure Failure (Clogged/Grease/Long-term)"
    if re.search(PATTERNS["structural_defect"], full_text):
        return "Physical Infrastructure Defect (Broken Cover/Pipe)"
    if re.search(PATTERNS["naturally_receded"], full_text):
        return "Naturally Receded (Unobserved)"
    if re.search(PATTERNS["hydraulic_surcharge"], full_text):
        return "Hydraulic Capacity Surcharge"
    if "น้ำท่วม" in full_text:
        return "Transient Surcharge Candidate"
    return "Other / Unclassified"

def download_monthly_bma_data(months=None, max_duration_hours=12.0, min_duration_hours=0.25):
    """
    Downloads monthly CSV datasets directly from official BMA Traffy Open Data API,
    extracts flood/drainage complaints, and computes duration and classifications.
    """
    if months is None:
        # Default to peak monsoon months
        months = ["bangkok_2022-09", "bangkok_2022-10", "bangkok_2023-09", "bangkok_2023-10"]

    all_flood_records = []

    for month_file in months:
        print(f"\n--- Downloading official BMA dataset: {month_file} ---")
        params = DEFAULT_PARAMS.copy()
        params["file_name"] = month_file

        try:
            res = requests.get(API_ENDPOINT, params=params, stream=True, timeout=60)
            res.raise_for_status()
            
            # Stream and parse CSV
            df_month = pd.read_csv(io.BytesIO(res.content), low_memory=False)
            print(f"Downloaded {len(df_month)} total municipal records for {month_file}")
            
            # Filter for flood/drainage tickets
            mask_flood = (
                df_month["type"].str.contains("น้ำท่วม|ท่อ|ระบายน้ำ", na=False) |
                df_month["comment"].str.contains("น้ำท่วม|น้ำรอระบาย", na=False)
            )
            df_floods = df_month[mask_flood].copy()
            print(f"Found {len(df_floods)} flood/drainage tickets in {month_file}")
            
            all_flood_records.append(df_floods)
        except Exception as e:
            print(f"Error downloading {month_file}: {e}", file=sys.stderr)

    if not all_flood_records:
        print("No records retrieved from BMA API.")
        return pd.DataFrame()

    combined_df = pd.concat(all_flood_records, ignore_index=True)
    print(f"\n=================================================")
    print(f"Total Combined Flood Records Downloaded: {len(combined_df)}")
    print(f"=================================================")

    # Parse coordinates coords: "100.50193,13.75337"
    def parse_coords(coord_str):
        if not isinstance(coord_str, str) or "," not in coord_str:
            return None, None
        try:
            parts = coord_str.split(",")
            return float(parts[1].strip()), float(parts[0].strip()) # lat, lon
        except Exception:
            return None, None

    coords_parsed = combined_df["coords"].apply(parse_coords)
    combined_df["latitude"] = [c[0] for c in coords_parsed]
    combined_df["longitude"] = [c[1] for c in coords_parsed]

    # Convert timestamps and compute duration in hours
    combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"], errors="coerce")
    combined_df["timestamp_inprogress"] = pd.to_datetime(combined_df["timestamp_inprogress"], errors="coerce")
    combined_df["timestamp_finished"] = pd.to_datetime(combined_df["timestamp_finished"], errors="coerce")

    # Use official BMA total duration in minutes converted to hours
    combined_df["duration_hours"] = pd.to_numeric(combined_df["duration_minutes_total"], errors="coerce") / 60.0
    combined_df["dispatch_hours"] = pd.to_numeric(combined_df["duration_minutes_inprogress"], errors="coerce") / 60.0
    combined_df["work_hours"] = pd.to_numeric(combined_df["duration_minutes_finished"], errors="coerce") / 60.0

    # Classify complaints
    combined_df["drain_category"] = combined_df.apply(
        lambda r: classify_bangkok_text(r.get("comment"), r.get("type")), axis=1
    )

    # Filter for completed empty cases within transient duration window
    transient_categories = [
        "Naturally Receded (Unobserved)",
        "Hydraulic Capacity Surcharge",
        "Transient Surcharge Candidate"
    ]
    
    empty_cases_df = combined_df[
        combined_df["drain_category"].isin(transient_categories) &
        (combined_df["state"] == "เสร็จสิ้น") &
        (combined_df["duration_hours"] >= min_duration_hours) &
        (combined_df["duration_hours"] <= max_duration_hours)
    ].copy()

    empty_cases_df.sort_values(by="timestamp", ascending=False, inplace=True)
    return empty_cases_df, combined_df

def main():
    months_to_fetch = ["bangkok_2022-09"]
    empty_df, all_df = download_monthly_bma_data(
        months=months_to_fetch, 
        max_duration_hours=12.0, 
        min_duration_hours=0.25
    )

    if empty_df.empty:
        print("No empty cases matched the criteria.")
        return

    print("\n--- Summary: Bangkok Official BMA Transient Flood Empty Cases ---")
    print(f"Total Raw Flood Records:          {len(all_df)}")
    print(f"Total Validated Empty Cases (<12h): {len(empty_df)}")
    print(f"Mean Resolution Duration:         {empty_df['duration_hours'].mean():.2f} hours")
    print(f"Median Resolution Duration:       {empty_df['duration_hours'].median():.2f} hours")

    print("\nBreakdown by Drain Category:")
    print(empty_df["drain_category"].value_counts().to_string())

    print("\nBreakdown by District (Top 10):")
    print(empty_df["district"].value_counts().head(10).to_string())

    output_filename = "bangkok_bma_official_empty_cases.csv"
    empty_df.to_csv(output_filename, index=False)
    print(f"\nSaved {len(empty_df)} validated records to '{output_filename}'")

if __name__ == "__main__":
    main()
