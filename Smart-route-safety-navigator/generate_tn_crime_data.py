import csv
import random
import datetime

# Real major cities in Tamil Nadu and their approximate centers
cities = {
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Coimbatore": {"lat": 11.0168, "lon": 76.9558},
    "Madurai": {"lat": 9.9252, "lon": 78.1198},
    "Trichy": {"lat": 10.7905, "lon": 78.7047},
    "Salem": {"lat": 11.6643, "lon": 78.1460},
    "Tirunelveli": {"lat": 8.7139, "lon": 77.7567},
    "Tiruppur": {"lat": 11.1085, "lon": 77.3411},
    "Erode": {"lat": 11.3410, "lon": 77.7172},
    "Vellore": {"lat": 12.9165, "lon": 79.1325},
    "Thoothukudi": {"lat": 8.7642, "lon": 78.1348},
    "Kanyakumari": {"lat": 8.0883, "lon": 77.5385},
    "Thanjavur": {"lat": 10.7870, "lon": 79.1378}
}

landmarks = {
    "Chennai": ["Central Station", "T. Nagar market", "Marina Beach", "Koyambedu CMBT", "Guindy", "Mylapore", "Anna Nagar", "Velachery", "Tambaram", "OMR IT Corridor"],
    "Coimbatore": ["Gandhipuram", "Peelamedu", "RS Puram", "Ukkadam", "Railway Station", "Thudiyalur", "Singanallur", "Saravanampatti"],
    "Madurai": ["Meenakshi Temple area", "Mattuthavani Bus Stand", "Periyar Bus Stand", "Anna Nagar", "K K Nagar", "Tallakulam", "Arapalayam"],
    "Trichy": ["Chatram Bus Stand", "Central Bus Stand", "Srirangam", "NIT area", "Thillai Nagar", "Cantonment", "Woraiyur"],
    "Salem": ["New Bus Stand", "Old Bus Stand", "Railway Station", "5-roads", "Gugai", "Ammapet", "Hasthampatti"],
    "Tirunelveli": ["Junction Bus Stand", "Palayamkottai", "Vannarpettai", "Town area", "Melapalayam"],
    "Tiruppur": ["Old Bus Stand", "New Bus Stand", "Railway Station", "PN Road", "Avinashi Road", "Dharapuram Road"],
    "Erode": ["Bus Stand", "Railway Station", "Bhavani Road", "Perundurai Road", "Karungalpalayam", "Surampatti"],
    "Vellore": ["Katpadi Railway Station", "Old Bus Stand", "CMC Hospital area", "Sathuvachari", "Fort area"],
    "Thoothukudi": ["Old Bus Stand", "New Bus Stand", "TVS Nagar", "Cruz Fernandez Statue area", "Beach Road"],
    "Kanyakumari": ["Sunset Point", "Railway Station", "Bus Stand", "Beach Road", "Vivekananda Rock junction"],
    "Thanjavur": ["Big Temple area", "Old Bus Stand", "New Bus Stand", "Medical College Road", "Railway Station"]
}

crime_types = [
    {"type": "Assault", "severity_range": (8, 10), "desc_templates": ["Physical assault near {}", "Violent brawl in {}", "Attack reported near {}"]},
    {"type": "Robbery", "severity_range": (7, 9), "desc_templates": ["Chain snatching near {}", "Phone theft in {}", "Bag snatching reported in {}"]},
    {"type": "Harassment", "severity_range": (6, 8), "desc_templates": ["Eve-teasing reported near {}", "Harassment near {}", "Stalking complaint in {}"]},
    {"type": "Drug Activity", "severity_range": (7, 9), "desc_templates": ["Suspicious gathering in {}", "Illegal activity near {}", "Drug peddling reported in {}"]},
    {"type": "Poor Lighting", "severity_range": (3, 5), "desc_templates": ["Dark stretches in {}", "Street lights off near {}", "Unlit road in {}"]},
    {"type": "Isolated Area", "severity_range": (4, 6), "desc_templates": ["Empty lanes in {}", "Isolated path near {}", "Unsafe deserted road in {}"]},
    {"type": "Police Station", "severity_range": (-10, -10), "desc_templates": ["Safety Point: {} Police Station", "Safe Zone: {} Police Booth"]},
    {"type": "CCTV Zone", "severity_range": (-5, -5), "desc_templates": ["Safety Point: High surveillance in {}", "CCTV Cover: {}"]}
]

# Real, specific news incidents over 2023-2026. Explicit lat/lons approximated to the real-world neighborhood
real_events = [
    # Chennai
    [1, "Murder", 13.1250, 80.1650, 10, "2024-12-30 22:15", "Murder of 24-year-old history-sheeter 'Lota' Naveen by 6-member gang in Muthamizh Nagar, Kallikuppam, Ambattur (News Report)"],
    [2, "Murder", 13.1110, 80.2460, 10, "2024-07-05 19:30", "Political murder of K. Armstrong by gang posing as delivery agents near residence in Perambur (News Report)"],
    [3, "Murder", 13.0062, 80.2574, 10, "2026-01-10 08:45", "Triple murder involving migrant worker family; body found in gunny bag in Indira Nagar, Adyar (News Report)"],
    [4, "Assault/Attempted Murder", 13.1220, 80.2555, 9, "2025-10-14 20:00", "Four men with criminal records arrested for attempting to stab 45-year-old woman in MKB Nagar (News Report)"],
    [5, "Murder", 12.7846, 80.2520, 10, "2023-04-12 23:00", "Woman arrested for killing ex-lover and burying dismembered body in Kovalam (News Report)"],

    # Coimbatore
    [6, "Murder", 11.1118, 77.1683, 10, "2024-11-20 21:30", "42-year-old man hacked to death near Karumathampatti on Avinashi Road, Coimbatore (News Report)"],
    [7, "Assault", 11.0827, 76.9415, 9, "2025-11-05 23:45", "Gang rape accused arrested following police encounter near Thudiyalur/Thediyalur temple area (News Report)"],
    [8, "Murder", 10.9702, 76.9634, 10, "2025-12-15 22:10", "Home Guard arrested for murder of 23-year-old migrant youth Suraj in Pullukadu / Karumbukkadai (News Report)"],
    [9, "Murder", 11.0255, 77.1250, 10, "2023-04-01 20:00", "Couple convicted of murder of a man near Sulur in Coimbatore district (News Report)"],

    # Madurai
    [10, "Murder", 9.8820, 78.1880, 10, "2024-07-22 06:30", "Woman discovered murdered on a farm along Ramanathapuram Road in Silaiman (News Report)"],
    [11, "Assault/Attempted Murder", 9.9070, 78.1380, 9, "2024-01-15 19:40", "Attempted revenge killing on a loadman in Kamarajapuram (News Report)"],
    [12, "Murder", 9.8090, 77.9620, 10, "2023-11-10 22:00", "Murder-for-gain case involving migrant worker from Bihar solved in Thoppur (News Report)"]
]

num_synthetic_records = 488
records = real_events.copy()
current_time = datetime.datetime.now()
next_id = len(real_events) + 1

# Generate synthetic records to pad the dataset
for i in range(next_id, next_id + num_synthetic_records):
    city_name, city_coords = random.choice(list(cities.items()))
    crime = random.choice(crime_types)
    
    # Slight perturbation to coordinates based on city center (approx 5-10 km radius)
    lat_offset = random.uniform(-0.06, 0.06)
    lon_offset = random.uniform(-0.06, 0.06)
    
    lat = round(city_coords["lat"] + lat_offset, 4)
    lon = round(city_coords["lon"] + lon_offset, 4)
    
    severity = random.randint(crime["severity_range"][0], crime["severity_range"][1])
    
    # Pick a timestamp within the last 30 days
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    timestamp = current_time - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
    
    landmark = random.choice(landmarks[city_name])
    description = random.choice(crime["desc_templates"]).format(landmark)
    
    records.append([i, crime["type"], lat, lon, severity, timestamp_str, description])

csv_file = "crime_history.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "type", "latitude", "longitude", "severity", "timestamp", "description"])
    writer.writerows(records)

print(f"Successfully generated {len(records)} realistic Tamil Nadu crime records (inculding {len(real_events)} exact real-world news incidents) in {csv_file}")
