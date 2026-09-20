import requests
import pandas as pd

ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

# Pull 2,000 recent closed DEP complaints that involve flooding or catch basins specifically
params = {
    "$select": "descriptor, resolution_description",
    "$where": """
        agency = 'DEP'
        AND complaint_type = 'Sewer'
        AND descriptor in ('Street Flooding (SJ)', 'Catch Basin Clogged/Flooding (SC)', 'Sewer Backup (SA)')
        AND closed_date IS NOT NULL
        AND resolution_description IS NOT NULL
    """,
    "$limit": 2000
}

response = requests.get(ENDPOINT, params=params)
data = response.json()

if not data:
    print("No records found with those descriptors.")
else:
    df = pd.DataFrame(data)
    print("--- TOP 10 MOST COMMON RESOLUTION DESCRIPTIONS ---")
    print(df["resolution_description"].value_counts().head(10))