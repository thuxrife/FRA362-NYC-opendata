import re
import sys
import ast
import time
import requests
import pandas as pd

API_ENDPOINT = "https://publicapi.traffy.in.th/share/search"
BMA_OPEN_DATA_URL = "https://media.githubusercontent.com/media/motethansen/bkk-traffy-data/main/df_traffyfull.csv"

# Lexical Regex Patterns for Bangkok Municipal Complaints (Method A)
PATTERNS = {
    # 1. Chronic or physical structural defects (Exclude from Empty Cases)
    "chronic_clog": r"ไขมัน|ขยะอุดตัน|ลอกท่อ|ทุก\s*\d+\s*เดือน|เป็นประจำ|ตันสะสม|เรื้อรัง|มากกว่า\s*1\s*สัปดาห์|นานแล้ว|ตะไคร่|ไม่มีท่อ",
    "structural_defect": r"ฝาท่อแตก|ฝาท่อชำรุด|ท่อทรุด|ท่อแตก|เหล็กยื่น|พัง|เป็นหลุม|ฝาท่อพัง",
    
    # 2. Transient Flooding / Capacity Surcharge (Empty Case Candidates)
    "hydraulic_surcharge": r"ระบายไม่ทัน|น้ำรอระบาย|ฝนตกหนัก|ขังช่วงฝน|เวลาฝนตก|ระบายช้า|ฝนตกน้ำท่วม",
    "naturally_receded": r"น้ำแห้งแล้ว|ลดลงแล้ว|แห้งเป็นปกติ|ไม่พบปัญหาน้ำท่วม|น้ำแห้ง|น้ำลด"
}

def classify_bangkok_text(text: str, problem_type: str = "") -> str:
    """
    Classifies a Traffy Fondue complaint using Method A Lexical / Regex Pattern Matching.
    """
    full_text = f"{text or ''} {problem_type or ''}".lower()
    
    # Priority 1: Exclude chronic / structural issues
    if re.search(PATTERNS["chronic_clog"], full_text):
        return "Chronic Infrastructure Failure (Clogged/Grease/Long-term)"
    if re.search(PATTERNS["structural_defect"], full_text):
        return "Physical Infrastructure Defect (Broken Cover/Pipe)"
        
    # Priority 2: Check for explicit self-resolved / receded reports
    if re.search(PATTERNS["naturally_receded"], full_text):
        return "Naturally Receded (Unobserved)"
        
    # Priority 3: Check for storm-driven hydraulic capacity surcharge
    if re.search(PATTERNS["hydraulic_surcharge"], full_text):
        return "Hydraulic Capacity Surcharge"
        
    # Priority 4: General flood report without chronic flags
    if "น้ำท่วม" in full_text:
        return "Transient Surcharge Candidate"
        
    return "Other / Unclassified"

def fetch_bma_full_open_dataset():
    """
    Streams and extracts all flood/drainage records from the full BMA open data repository.
    """
    print("Streaming full BMA Traffy Fondue Open Dataset...")
    rows = []
    
    for i, chunk in enumerate(pd.read_csv(BMA_OPEN_DATA_URL, chunksize=50000, low_memory=False)):
        mask = (
            chunk["type"].str.contains("น้ำท่วม|ท่อ|ระบายน้ำ", na=False) |
            chunk["comment"].str.contains("น้ำท่วม|น้ำรอระบาย|ท่อตัน", na=False)
        )
        filtered = chunk[mask].copy()
        
        for _, r in filtered.iterrows():
            coords_raw = r.get("coords")
            lon, lat = None, None
            if isinstance(coords_raw, str):
                try:
                    parsed = ast.literal_eval(coords_raw)
                    if len(parsed) >= 2:
                        lon, lat = float(parsed[0]), float(parsed[1])
                except Exception:
                    pass

            comment = r.get("comment", "")
            p_type = r.get("type", "")
            category = classify_bangkok_text(comment, p_type)

            rows.append({
                "ticket_id": r.get("ticket_id"),
                "timestamp": r.get("timestamp"),
                "latitude": lat,
                "longitude": lon,
                "district": r.get("district"),
                "subdistrict": r.get("subdistrict"),
                "address": r.get("address"),
                "problem_type": p_type,
                "description": comment,
                "state": r.get("state"),
                "photo_url": r.get("photo"),
                "after_photo_url": r.get("after_photo"),
                "drain_category": category
            })
            
        print(f"Processed chunk {i+1}: accumulated {len(rows)} matching flood/drainage records")

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df.sort_values(by="timestamp", ascending=False, inplace=True)
    return df

def main():
    df = fetch_bma_full_open_dataset()
    
    if df.empty:
        print("No flood cases returned.")
        return

    print("\n--- Summary: Full Bangkok Flooding Incidents by Category (Method A) ---")
    print(df["drain_category"].value_counts().to_string())

    # Filter for transient empty case candidates that reached completion ('เสร็จสิ้น')
    transient_categories = [
        "Naturally Receded (Unobserved)",
        "Hydraulic Capacity Surcharge",
        "Transient Surcharge Candidate"
    ]
    empty_cases_df = df[
        df["drain_category"].isin(transient_categories) & 
        (df["state"] == "เสร็จสิ้น")
    ].copy()

    print(f"\n=======================================================")
    print(f"Total Validated Completed Transient Flood Cases: {len(empty_cases_df)} of {len(df)}")
    print(f"=======================================================")
    
    print("\nTop 15 Districts with Highest Transient Flooding in Bangkok:")
    print(empty_cases_df["district"].value_counts().head(15).to_string())

    output_filename = "bangkok_traffy_self_resolved_floods.csv"
    empty_cases_df.to_csv(output_filename, index=False)
    print(f"\nSaved {len(empty_cases_df)} validated Bangkok records to '{output_filename}'")

if __name__ == "__main__":
    main()
