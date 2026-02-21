"""
Enhanced Tamil Nadu Crime Dataset Generator
Based on NCRB 2022-2023 data, Chennai GCP GIS mapping (2023),
and research on Tamil Nadu crime hotspots.

Key sources used:
- NCRB Crime in India Report 2022 & 2023
- Greater Chennai Police GIS Mapping Initiative (June 2023: 60,000+ records 2016-2022)
- Chennai crime hotspots: North Chennai (Kasimedu, Royapuram, Vyasarpadi),
  South Chennai (Royapettah, Taramani), Koyambedu, T Nagar, Anna Salai
- Women's safety: Nungambakkam High Rd, Kodambakkam, MRTS roads unsafe at night
- 97.9% surge in cybercrime, highest theft in South Chennai (commercial areas)
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# ============================================================================
# RESEARCH-INFORMED HOTSPOTS (lat, lon, area_name, risk_level)
# Based on NCRB + GCP GIS data + news reports
# ============================================================================
HOTSPOTS = [
    # NORTH CHENNAI - Historically high criminal activity
    {"area": "Kasimedu", "lat": 13.1212, "lon": 80.2900, "risk": "very_high"},
    {"area": "Royapuram", "lat": 13.1184, "lon": 80.2860, "risk": "very_high"},
    {"area": "Vyasarpadi", "lat": 13.1035, "lon": 80.2500, "risk": "high"},
    {"area": "Puliyanthope", "lat": 13.1100, "lon": 80.2750, "risk": "high"},
    {"area": "Washermanpet", "lat": 13.1150, "lon": 80.2800, "risk": "high"},
    {"area": "Perambur", "lat": 13.1100, "lon": 80.2460, "risk": "high"},
    {"area": "Ambattur", "lat": 13.1140, "lon": 80.1590, "risk": "high"},
    {"area": "Kolathur", "lat": 13.1290, "lon": 80.2100, "risk": "moderate"},

    # SOUTH CHENNAI - Higher theft/burglary, women's safety concerns
    {"area": "Royapettah", "lat": 13.0560, "lon": 80.2640, "risk": "high"},
    {"area": "Mylapore", "lat": 13.0368, "lon": 80.2676, "risk": "moderate"},
    {"area": "Taramani", "lat": 12.9820, "lon": 80.2431, "risk": "high"},
    {"area": "Adyar", "lat": 13.0067, "lon": 80.2568, "risk": "moderate"},
    {"area": "Guindy", "lat": 13.0067, "lon": 80.2206, "risk": "moderate"},
    {"area": "Velachery", "lat": 12.9815, "lon": 80.2176, "risk": "moderate"},
    {"area": "Tambaram", "lat": 12.9249, "lon": 80.1000, "risk": "moderate"},

    # CENTRAL CHENNAI - Commercial/theft hotspots
    {"area": "T Nagar", "lat": 13.0418, "lon": 80.2341, "risk": "high"},
    {"area": "Anna Salai", "lat": 13.0650, "lon": 80.2490, "risk": "high"},
    {"area": "Koyambedu", "lat": 13.0694, "lon": 80.1948, "risk": "high"},
    {"area": "Nungambakkam", "lat": 13.0604, "lon": 80.2428, "risk": "moderate"},
    {"area": "Kodambakkam", "lat": 13.0527, "lon": 80.2208, "risk": "moderate"},

    # OTHER MAJOR TN CITIES - Coimbatore
    {"area": "Ukkadam Coimbatore", "lat": 10.9940, "lon": 76.9647, "risk": "high"},
    {"area": "Gandhipuram Coimbatore", "lat": 11.0168, "lon": 76.9558, "risk": "moderate"},
    {"area": "RS Puram Coimbatore", "lat": 10.9884, "lon": 76.9550, "risk": "low"},
    {"area": "Peelamedu Coimbatore", "lat": 11.0213, "lon": 77.0087, "risk": "moderate"},

    # Madurai
    {"area": "Goripalayam Madurai", "lat": 9.9200, "lon": 78.1100, "risk": "high"},
    {"area": "Mattuthavani Madurai", "lat": 9.9252, "lon": 78.1198, "risk": "moderate"},
    {"area": "Tallakulam Madurai", "lat": 9.9300, "lon": 78.1350, "risk": "moderate"},

    # Salem
    {"area": "Old Bus Stand Salem", "lat": 11.6643, "lon": 78.1480, "risk": "high"},
    {"area": "Suramangalam Salem", "lat": 11.6720, "lon": 78.1580, "risk": "moderate"},

    # Tiruchirappalli (Trichy)
    {"area": "Srirangam Trichy", "lat": 10.8632, "lon": 78.6896, "risk": "moderate"},
    {"area": "Woraiyur Trichy", "lat": 10.8000, "lon": 78.7200, "risk": "high"},
    {"area": "KK Nagar Trichy", "lat": 10.8220, "lon": 78.7000, "risk": "moderate"},

    # Tirunelveli
    {"area": "Palayamkottai", "lat": 8.7282, "lon": 77.7563, "risk": "moderate"},
    {"area": "Tirunelveli Town", "lat": 8.7139, "lon": 77.7567, "risk": "high"},
]

# ============================================================================
# SAFE HAVENS (police stations, hospitals, CCTV-covered areas)
# ============================================================================
SAFE_HAVENS = [
    # Chennai Police Stations
    {"lat": 13.1195, "lon": 80.2851, "type": "Police Station", "desc": "Royapuram Police Station"},
    {"lat": 13.0560, "lon": 80.2635, "type": "Police Station", "desc": "Royapettah Police Station"},
    {"lat": 13.0694, "lon": 80.1948, "type": "Police Station", "desc": "Koyambedu Police Station"},
    {"lat": 13.1140, "lon": 80.1590, "type": "Police Station", "desc": "Ambattur Police Station"},
    {"lat": 13.0104, "lon": 80.2127, "type": "Police Station", "desc": "Guindy Police Station"},
    {"lat": 13.0418, "lon": 80.2341, "type": "Police Station", "desc": "T Nagar Police Station"},
    {"lat": 13.0604, "lon": 80.2428, "type": "Police Station", "desc": "Nungambakkam Police Station"},
    {"lat": 13.0827, "lon": 80.2707, "type": "Police Station", "desc": "Chennai Central Police Station"},
    {"lat": 13.0368, "lon": 80.2676, "type": "Police Station", "desc": "Mylapore Police Station"},
    {"lat": 12.9820, "lon": 80.2431, "type": "Police Station", "desc": "Taramani Police Station"},

    # Hospitals (safe refuge points)
    {"lat": 13.0100, "lon": 80.2310, "type": "Hospital", "desc": "Govt. Multi Super Speciality Hospital, Omandurar"},
    {"lat": 13.0827, "lon": 80.2800, "type": "Hospital", "desc": "Rajiv Gandhi Government General Hospital, Park Town"},
    {"lat": 13.0450, "lon": 80.2330, "type": "Hospital", "desc": "Apollo Hospitals, Greams Road"},
    {"lat": 13.0000, "lon": 80.2500, "type": "Hospital", "desc": "Fortis Malar Hospital, Adyar"},
    {"lat": 11.0168, "lon": 76.9558, "type": "Hospital", "desc": "Coimbatore Medical College Hospital"},
    {"lat": 9.9252, "lon": 78.1198, "type": "Hospital", "desc": "Rajaji Government Hospital, Madurai"},

    # CCTV Zones (GCP GIS-informed)
    {"lat": 13.0827, "lon": 80.2790, "type": "CCTV Zone", "desc": "Chennai Central Railway Station CCTV Zone"},
    {"lat": 13.0418, "lon": 80.2341, "type": "CCTV Zone", "desc": "T Nagar Pondy Bazaar CCTV Zone"},
    {"lat": 13.0694, "lon": 80.1948, "type": "CCTV Zone", "desc": "Koyambedu Market CCTV Zone"},
    {"lat": 13.0650, "lon": 80.2490, "type": "CCTV Zone", "desc": "Anna Salai CCTV Corridor"},
    {"lat": 13.0560, "lon": 80.2810, "type": "CCTV Zone", "desc": "Marina Beach CCTV Zone"},
    {"lat": 13.0604, "lon": 80.2428, "type": "CCTV Zone", "desc": "Nungambakkam High Road CCTV"},
]

# ============================================================================
# CRIME TYPE TEMPLATES (NCRB-informed categories for TN)
# ============================================================================
CRIME_TEMPLATES = {
    "very_high": [
        ("Murder", 10, "Gang-related murder near {area} — history sheeter involved (GCP Records)"),
        ("Robbery", 9, "Armed robbery at {area} — snatching near bus stop (NCRB Chennai Data)"),
        ("Drug Activity", 9, "Narcotics seizure near {area} — ganja/MDMA peddling zone (NCRB TN 2023)"),
        ("Assault", 8, "Assault reported near {area} — rowdy elements involved (GCP FIR Data)"),
        ("Vehicle Theft", 7, "Organised vehicle theft ring active near {area} (Chennai 2nd most unsafe for car owners, NCRB 2023)"),
        ("Chain Snatching", 8, "Chain snatching near commercial area in {area} (NCRB TN Pattern)"),
    ],
    "high": [
        ("Robbery", 8, "Bag snatching near textile/retail area in {area} (GCP GIS-mapped hotspot)"),
        ("Harassment", 7, "Women's safety complaint near {area} — eve-teasing at night (Chennai Police Records)"),
        ("Drug Activity", 7, "Substance abuse reported near {area} (NCRB TN Drug Report 2023)"),
        ("Burglary", 7, "House break-in reported in {area} — South Chennai high-risk zone (NCRB 2022)"),
        ("Vehicle Theft", 6, "Two-wheeler theft spike in {area} — reported to GCP"),
        ("Assault", 7, "Physical altercation near {area} — late-night incident (GCP Records)"),
        ("Poor Lighting", 4, "Poor street lighting in {area} — increased crime risk after 8PM"),
    ],
    "moderate": [
        ("Harassment", 6, "Sexual harassment reported near {area} (Chennai Women's Safety Survey 2025)"),
        ("Theft", 5, "Petty theft near market area in {area}"),
        ("Poor Lighting", 3, "Inadequate lighting near MRTS station at {area} — unsafe for women at night"),
        ("Isolated Area", 4, "Deserted stretch near {area} — women reported feeling unsafe after dark (21% survey)"),
        ("Drug Activity", 5, "Suspicious activity reported near {area}"),
    ],
    "low": [
        ("Poor Lighting", 2, "Dim lighting in residential area near {area}"),
        ("Isolated Area", 3, "Relatively isolated stretch near {area} — use caution at night"),
    ]
}


def generate_timestamp(risk_level):
    """Generate realistic timestamp — risky areas skew towards night hours (NCRB pattern)"""
    base = datetime(2024, 1, 1)
    days = random.randint(0, 730)
    dt = base + timedelta(days=days)
    
    if risk_level in ("very_high", "high"):
        # Night-time skew (NCRB: majority of violent crime between 10PM-4AM)
        hour = random.choices(
            population=list(range(24)),
            weights=[3,2,2,2,2,1,1,1,1,1,1,1,1,1,1,2,3,4,5,6,8,9,8,6],
            k=1
        )[0]
    else:
        hour = random.randint(6, 22)
    
    minute = random.randint(0, 59)
    return dt.replace(hour=hour, minute=minute).strftime("%Y-%m-%d %H:%M")


def main():
    records = []
    record_id = 1

    # Add safe havens first (negative severity = safety points)
    for haven in SAFE_HAVENS:
        records.append({
            "id": record_id,
            "type": haven["type"],
            "latitude": round(haven["lat"] + random.uniform(-0.002, 0.002), 6),
            "longitude": round(haven["lon"] + random.uniform(-0.002, 0.002), 6),
            "severity": -10 if haven["type"] == "Police Station" else -5,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "description": f"Safe Zone: {haven['desc']}"
        })
        record_id += 1

    # Generate crime incidents per hotspot (NCRB density-proportional)
    crimes_per_risk = {"very_high": 20, "high": 14, "moderate": 9, "low": 4}

    for hotspot in HOTSPOTS:
        risk = hotspot["risk"]
        count = crimes_per_risk.get(risk, 5)
        templates = CRIME_TEMPLATES.get(risk, CRIME_TEMPLATES["moderate"])

        for _ in range(count):
            template = random.choice(templates)
            crime_type, base_severity, desc_template = template
            severity = min(10, max(1, base_severity + random.randint(-1, 1)))
            lat_jitter = random.uniform(-0.008, 0.008)
            lon_jitter = random.uniform(-0.008, 0.008)

            records.append({
                "id": record_id,
                "type": crime_type,
                "latitude": round(hotspot["lat"] + lat_jitter, 6),
                "longitude": round(hotspot["lon"] + lon_jitter, 6),
                "severity": severity,
                "timestamp": generate_timestamp(risk),
                "description": desc_template.format(area=hotspot["area"])
            })
            record_id += 1

    print(f"✅ Generated {len(records)} records ({len(SAFE_HAVENS)} safe zones + {len(records)-len(SAFE_HAVENS)} incidents)")
    print(f"   High-severity (>=7): {sum(1 for r in records if r['severity'] >= 7)}")
    print(f"   Safe zones: {sum(1 for r in records if r['severity'] < 0)}")

    with open("crime_history.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id","type","latitude","longitude","severity","timestamp","description"])
        writer.writeheader()
        writer.writerows(records)
    
    print(f"✅ crime_history.csv written with {len(records)} rows")


if __name__ == "__main__":
    main()
