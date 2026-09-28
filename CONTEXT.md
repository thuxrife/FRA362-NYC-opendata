# Project Context: Transient Urban Flooding Analysis (NYC 311 & Bangkok BMA Traffy Fondue)

## 1. Project Overview
This project (FRA362) analyzes and compares **transient (self-resolving) urban flooding events (Empty Cases)** across two global metropolitan areas:
1. **Dataset 1 (NYC)**: Open public 311 service requests from NYC Department of Environmental Protection (DEP).
2. **Dataset 2 (Bangkok)**: Official municipal incident reports from the **BMA Traffy Fondue Monthly Open Data API** (`https://publicapi.traffy.in.th/teamchadchart-stat-api/download/bangkok_monthly`).

Urban transient floods are short-lived ponding or surcharge events caused by high-intensity rainfall exceeding local drainage capacity or temporary catch basin surface blockages that dissipate naturally without permanent structural damage.

---

## 2. Codebase Architecture & Extraction Scripts

### A. [`inspect_resolutions.py`](file:///home/thuxrife/Documents/GitHub/FRA362-NYC-opendata/inspect_resolutions.py)
* **Purpose**: Exploratory analysis tool to inspect NYC DEP resolution patterns for sewer and flooding complaints.
* **Data Source**: NYC Open Data 311 SODA API (`https://data.cityofnewyork.us/resource/erm2-nwe9.json`).
* **Query Filters**: `agency = 'DEP'`, `complaint_type = 'Sewer'`, closed tickets with non-null resolution description.

---

### B. [`fetch_transient_floods.py`](file:///home/thuxrife/Documents/GitHub/FRA362-NYC-opendata/fetch_transient_floods.py)
* **Purpose**: Primary extraction and ETL script for NYC 311 transient flood events.
* **Core Pipeline Features**:
  1. **Automated Ingestion**: Queries NYC SODA endpoint `erm2-nwe9`.
  2. **Resolution Categorization**:
     * `Naturally Receded (Unobserved)`: Matches `"could not find the problem"`.
     * `Hydraulic Capacity Surcharge`: Matches `"surcharge conditions have been confirmed"`.
  3. **Duration Threshold**: Keeps cases with $0.25 \le \text{duration\_hours} \le 12.0$.
  4. **Output**: Exports to [`nyc_311_self_resolved_floods.csv`](file:///home/thuxrife/Documents/GitHub/FRA362-NYC-opendata/nyc_311_self_resolved_floods.csv).

---

### C. [`fetch_bma_monthly_floods.py`](file:///home/thuxrife/Documents/GitHub/FRA362-NYC-opendata/fetch_bma_monthly_floods.py) (Official BMA API Extractor)
* **Purpose**: Primary extraction and ETL script using the **Official BMA Traffy Monthly Open Data API** ([Notion Documentation](https://www.traffy.in.th/Open-Data-API-Document-26c430d4aa7b8010810dd37f04949d91)).
* **API Endpoint**: `https://publicapi.traffy.in.th/teamchadchart-stat-api/download/bangkok_monthly`
* **Core Pipeline Features**:
  1. **Direct Official Duration Metrics**:
     * Uses BMA's built-in `duration_minutes_total`, `duration_minutes_inprogress`, and `duration_minutes_finished`.
     * Converts to `duration_hours` for direct comparison with NYC.
  2. **Method A Lexical Classification**:
     * Filters out chronic clogs (`ไขมัน`, `ลอกท่อ`, `>1 สัปดาห์`) and hardware damage (`ฝาท่อแตก`, `ท่อทรุด`).
     * Classifies `Hydraulic Capacity Surcharge` (`ฝนตกหนัก`, `ระบายไม่ทัน`, `น้ำรอระบาย`) and `Naturally Receded` (`น้ำแห้งแล้ว`, `ลดลงแล้ว`).
  3. **Duration Thresholding**: Keeps completed tickets within the transient window ($0.25 \le \text{duration\_hours} \le 12.0$).
  4. **Output**: Exports to [`bangkok_bma_official_empty_cases.csv`](file:///home/thuxrife/Documents/GitHub/FRA362-NYC-opendata/bangkok_bma_official_empty_cases.csv).

---

## 3. Comparative Findings: NYC vs. Bangkok Empty Cases

| Metric | New York City (NYC 311 DEP) | Bangkok (BMA Official Traffy) |
|---|---|---|
| **Average (Mean) Clearance Duration** | **4.25 hours** | **4.29 hours** |
| **Median Clearance Duration** | **3.00 hours** | **3.45 hours** |
| **Transient Time Window** | $15\text{ mins} \le \Delta t \le 12\text{ hours}$ | $15\text{ mins} \le \Delta t \le 12\text{ hours}$ |
| **Ponding Trigger** | High rain burst exceeding catch basins | Monsoonal downpour exceeding soi drains (*"ระบายไม่ทัน"*) |
| **Clearance Verification** | Inspector: *"could not find the problem"* | BMA `photo_after` showing dry road |
| **Fastest District/Borough** | **Manhattan (3.53 hours)** | **Lak Si / Ratchathewi (~3.0 hours)** |
| **Slowest District/Borough** | **Staten Island (4.82 hours)** | **Prawet / Lat Krabang (~5.0 hours)** |

---

## 4. Execution Commands

```bash
# Activate Virtual Environment
source .venv/bin/activate

# Run NYC Extraction
python fetch_transient_floods.py

# Run Bangkok Official Monthly Extraction
python fetch_bma_monthly_floods.py
```
