import csv
import random
from datetime import datetime, timedelta
import math
import time
import os

# Configuration
INPUT_CSV = 'crime_history.csv'
OUTPUT_CSV = 'crime_realtime.csv'
UPDATE_INTERVAL_SECONDS = 300  # Generate new data every 5 minutes (for hackathon demo)
MAX_ACTIVE_INCIDENTS = 100

# Research-backed weights and factors
CRIME_TYPES = {
    'Assault': {'base_severity': 8, 'decay_rate': 0.1},      # Lingers longer, higher severity
    'Robbery': {'base_severity': 7, 'decay_rate': 0.15},     # Decays slightly faster
    'Harassment': {'base_severity': 6, 'decay_rate': 0.2},   # Mod severity, decays faster
    'Poor Lighting': {'base_severity': 4, 'decay_rate': 0.05}, # Environmental, decays very slowly
    'Isolated Area': {'base_severity': 5, 'decay_rate': 0.05}, # Environmental, decays very slowly
    'Drug Activity': {'base_severity': 7, 'decay_rate': 0.1},
    'Police Station': {'base_severity': -10, 'decay_rate': 0.0}, # Permanent safety zone
    'CCTV Zone': {'base_severity': -5, 'decay_rate': 0.0}       # Permanent safety zone
}

def load_base_data(filepath):
    """Loads historical data to build the initial state."""
    incidents = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert timestamp, if missing or invalid, use current time minus random days
                try:
                    dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M')
                except (ValueError, KeyError):
                    dt = datetime.now() - timedelta(days=random.randint(1, 30))
                
                # Parse existing data or assign defaults
                ctype = row.get('type', 'Unknown')
                severity = int(row.get('severity', CRIME_TYPES.get(ctype, {}).get('base_severity', 5)))
                
                incident = {
                    'id': row.get('id', f"H-{random.randint(1000,9999)}"),
                    'type': ctype,
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'base_severity': severity,
                    'dynamic_risk_score': severity, # Initial starting point
                    'timestamp': dt,
                    'last_updated': datetime.now(),
                    'time_decay_factor': CRIME_TYPES.get(ctype, {}).get('decay_rate', 0.1),
                    'hotspot_density': 1.0,
                    'safety_influence': 0.0,
                    'description': row.get('description', 'Historical incident')
                }
                incidents.append(incident)
    return incidents

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula to calculate distance between two lat/long points in km."""
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_time_weight(incident_type, current_time):
    """Routine Activity Theory: Adjust risk based on time of day."""
    hour = current_time.hour
    
    # Night time (8 PM to 4 AM) increases risk for certain crimes
    if 20 <= hour or hour <= 4:
        if incident_type in ['Assault', 'Robbery', 'Poor Lighting', 'Isolated Area']:
            return 1.3  # 30% risk increase at night
    # Daytime might increase risk of others (e.g. pickpocketing in crowds, though not heavily modeled here)
    elif 10 <= hour <= 18:
        if incident_type in ['Harassment']:
            return 1.1 
            
    return 1.0 # Standard weight

def calculate_hotspot_density(target_incident, all_incidents):
    """Hotspot Policing: Crimes cluster. Density increases risk multiplier."""
    close_incidents = 0
    RADIUS_KM = 0.5 # 500 meters
    
    # Don't compound safety zones with crime density
    if target_incident['base_severity'] < 0:
        return 1.0
        
    for inc in all_incidents:
        if inc['id'] != target_incident['id'] and inc['base_severity'] > 0:
            dist = calculate_distance(
                target_incident['latitude'], target_incident['longitude'],
                inc['latitude'], inc['longitude']
            )
            if dist <= RADIUS_KM:
                # Only count recent incidents (last 24 hours) for active clustering
                hours_diff = (datetime.now() - inc['timestamp']).total_seconds() / 3600
                if hours_diff < 24:
                    close_incidents += 1
                    
    # Cap the multiplier at 2.0 (100% increase)
    return min(1.0 + (close_incidents * 0.15), 2.0)

def calculate_safety_influence(target_incident, all_incidents):
    """Capable Guardian Theory: Police stations/CCTV reduce nearby risk."""
    influence = 0.0
    RADIUS_KM = 1.0 # 1km influence radius for safety nodes
    
    if target_incident['base_severity'] < 0:
        return 0.0 # Safety nodes don't reduce their own score
        
    for inc in all_incidents:
        if inc['base_severity'] < 0: # It's a safety node
            dist = calculate_distance(
                target_incident['latitude'], target_incident['longitude'],
                inc['latitude'], inc['longitude']
            )
            if dist <= RADIUS_KM:
                # Stronger influence the closer it is
                proximity_factor = 1.0 - (dist / RADIUS_KM)
                influence += abs(inc['base_severity']) * proximity_factor
                
    return influence

def update_dynamic_scores(incidents, current_time):
    """Recalculates the dynamic risk for all active incidents."""
    for inc in incidents:
        # Safety infrastructure doesn't decay
        if inc['base_severity'] < 0:
             inc['dynamic_risk_score'] = inc['base_severity']
             inc['last_updated'] = current_time
             continue
             
        hours_elapsed = (current_time - inc['timestamp']).total_seconds() / 3600
        
        # 1. Time Decay (Recency Factor)
        # Formula: e^(-decay_rate * hours)
        recency_factor = math.exp(-inc['time_decay_factor'] * hours_elapsed)
        
        # 2. Time-of-Day Weight
        time_weight = get_time_weight(inc['type'], current_time)
        
        # 3. Hotspot Density
        inc['hotspot_density'] = calculate_hotspot_density(inc, incidents)
        
        # 4. Safety Influence (Capable Guardian)
        inc['safety_influence'] = calculate_safety_influence(inc, incidents)
        
        # Final Formula calculation
        # Risk = (Base * TimeWeight * Recency * Hotspot) - Safety
        raw_score = (inc['base_severity'] * time_weight * recency_factor * inc['hotspot_density']) - inc['safety_influence']
        
        # Floor at 0.0, cap at 10.0
        inc['dynamic_risk_score'] = round(max(0.0, min(10.0, raw_score)), 2)
        inc['last_updated'] = current_time

    return incidents

def generate_new_incident(existing_incidents):
    """Near-Repeat Theory: Spawns a new incident, heavily weighted near existing hotspots."""
    # Simple bounding box for Chennai area (based on historical data)
    lat_min, lat_max = 12.8, 13.2
    lon_min, lon_max = 80.1, 80.3
    
    ctype = random.choice([k for k, v in CRIME_TYPES.items() if v['base_severity'] > 0])
    
    # 70% chance to spawn near an existing recent crime (Near-Repeat theory)
    # 30% chance to spawn randomly
    if random.random() < 0.7 and existing_incidents:
        # Pick a random crime incident to cluster near
        crime_incidents = [i for i in existing_incidents if i['base_severity'] > 0]
        if crime_incidents:
            anchor = random.choice(crime_incidents)
            # Spawn within ~500m to 2km
            lat_offset = random.uniform(-0.015, 0.015) 
            lon_offset = random.uniform(-0.015, 0.015)
            new_lat = anchor['latitude'] + lat_offset
            new_lon = anchor['longitude'] + lon_offset
        else:
            new_lat = random.uniform(lat_min, lat_max)
            new_lon = random.uniform(lon_min, lon_max)
    else:
        new_lat = random.uniform(lat_min, lat_max)
        new_lon = random.uniform(lon_min, lon_max)
        
    incident_id = f"SIM-{int(time.time())}-{random.randint(10,99)}"
    
    config = CRIME_TYPES[ctype]
    dt = datetime.now()
    
    new_incident = {
        'id': incident_id,
        'type': ctype,
        'latitude': round(new_lat, 4),
        'longitude': round(new_lon, 4),
        'base_severity': config['base_severity'],
        'dynamic_risk_score': config['base_severity'], # Will be updated in next cycle
        'timestamp': dt,
        'last_updated': dt,
        'time_decay_factor': config['decay_rate'],
        'hotspot_density': 1.0,
        'safety_influence': 0.0,
        'description': f"Simulated {ctype.lower()} reported via dispatch feed."
    }
    return new_incident


def save_to_csv(incidents, filepath):
    """Writes the current state out to CSV."""
    if not incidents:
        return
        
    fieldnames = ['id', 'type', 'latitude', 'longitude', 'base_severity', 
                  'dynamic_risk_score', 'timestamp', 'last_updated', 
                  'time_decay_factor', 'hotspot_density', 'safety_influence', 'description']
                  
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Sort by dynamic risk score descending for easier viewing
        sorted_incidents = sorted(incidents, key=lambda x: x['dynamic_risk_score'], reverse=True)
        
        for inc in sorted_incidents:
            # Format dates for CSV
            row = inc.copy()
            row['timestamp'] = inc['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            row['last_updated'] = inc['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Format floats
            row['hotspot_density'] = f"{inc['hotspot_density']:.2f}"
            row['safety_influence'] = f"{inc['safety_influence']:.2f}"
            
            writer.writerow(row)
            
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Wrote {len(incidents)} records to {filepath}")

def run_simulation(duration_minutes=None):
    """Main loop driving the realtime simulation."""
    print("Initializing Real-Time Crime Simulation Engine...")
    incidents = load_base_data(INPUT_CSV)
    print(f"Loaded {len(incidents)} historical incidents.")
    
    start_time = datetime.now()
    
    try:
        while True:
            current_time = datetime.now()
            
            # Stop condition for testing/hackathon
            if duration_minutes and (current_time - start_time).total_seconds() > (duration_minutes * 60):
                print("Simulation duration reached. Exiting.")
                break
                
            # 1. Purge very old/irrelevant events (Score < 0.5) to keep dataset light
            # Keep safety nodes and recent events
            pruned_incidents = [
                inc for inc in incidents 
                if inc['dynamic_risk_score'] >= 0.5 or inc['base_severity'] < 0 or (current_time - inc['timestamp']).total_seconds() < 3600
            ]
            
            # 2. Simulate new API feeds injects (1 to 3 new incidents per cycle)
            if len(pruned_incidents) < MAX_ACTIVE_INCIDENTS:
                 num_new = random.randint(1, 3)
                 for _ in range(num_new):
                     pruned_incidents.append(generate_new_incident(pruned_incidents))
            
            # 3. Recalculate mathematical risk for every node based on Current Time
            updated_incidents = update_dynamic_scores(pruned_incidents, current_time)
            incidents = updated_incidents
            
            # 4. Flush to output CSV for Flask routing algorithm to ingest
            save_to_csv(incidents, OUTPUT_CSV)
            
            print(f"Sleeping for {UPDATE_INTERVAL_SECONDS} seconds...\n")
            time.sleep(UPDATE_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\nSimulation terminated by user.")

if __name__ == "__main__":
    # If run directly as a script, do a single pass to generate the output CSV immediately
    # Then it could optionally loop. For now, running a few loop iterations rapidly to populate data.
    print("Running initial pass to establish dynamic scores...")
    incidents = load_base_data(INPUT_CSV)
    
    # Inject some fresh incidents right away to show "now" data
    for _ in range(5):
       incidents.append(generate_new_incident(incidents))
       
    update_dynamic_scores(incidents, datetime.now())
    save_to_csv(incidents, OUTPUT_CSV)
    
    # Uncomment to run continuous loop (disabled for standard script execution)
    # run_simulation()

