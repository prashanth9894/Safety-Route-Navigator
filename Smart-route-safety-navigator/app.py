from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import math
from datetime import datetime

# ============================================================================
# TIME MULTIPLIER (NCRB-informed: night crime risk is substantially higher)
# Based on Tamil Nadu crime patterns: night incidents 10PM-4AM are 2x more dangerous
# ============================================================================

def get_time_risk_multiplier(hour=None):
    """Return a risk multiplier based on the time of day"""
    if hour is None:
        hour = datetime.now().hour
    if 22 <= hour or hour < 4:   # 10PM - 4AM: peak danger window
        return 1.8, "🌙 Night Travel Risk: HIGH"
    elif 18 <= hour < 22:        # 6PM - 10PM: elevated risk window
        return 1.3, "🌆 Evening Travel Risk: MODERATE"
    elif 4 <= hour < 7:          # 4AM - 7AM: early morning
        return 1.2, "🌅 Early Morning Risk: SLIGHTLY ELEVATED"
    else:
        return 1.0, "☀️ Daytime Risk: NORMAL"

app = Flask(__name__)

# ============================================================================
# HELPER FUNCTIONS & DATA LOADING
# ============================================================================

# Global cache for the dataset to prevent Disk I/O on every API request
_CRIME_DF = None

def get_crime_df():
    """Load or return the cached crime dataset securely"""
    global _CRIME_DF
    if _CRIME_DF is None:
        try:
            _CRIME_DF = pd.read_csv('crime_history.csv')
            print(f"✅ Loaded {_CRIME_DF.shape[0]} records into memory.")
        except Exception as e:
            print(f"❌ Error loading dataset: {str(e)}")
            # Fallback empty dataframe to prevent hard crashes
            _CRIME_DF = pd.DataFrame(columns=['latitude', 'longitude', 'type', 'description', 'severity'])
    return _CRIME_DF

def get_coordinates(place_name: str):
    """Convert place name to coordinates using Nominatim"""
    url = f"https://nominatim.openstreetmap.org/search?q={place_name}&format=json&limit=1"
    headers = {'User-Agent': 'SafeRouteNavigator/1.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5).json()
        if response:
            return response[0]['lon'], response[0]['lat']
        return None
    except Exception:
        return None

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km"""
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_safety(geometry, crime_df, time_multiplier=1.0):
    """Calculate safety score for a route based on crime proximity, time-adjusted"""
    total_risk = 0
    unsafe_pins = []
    
    # Sample every 5th point to optimize performance
    for i in range(0, len(geometry), 5):
        lon, lat = geometry[i]
        
        for _, crime in crime_df.iterrows():
            distance = haversine(lat, lon, float(crime['latitude']), float(crime['longitude']))
            
            # Within 300m radius
            if distance < 0.3:
                severity = crime['severity']
                
                # Apply time-of-day multiplier to positive (danger) severities
                if severity < 0:
                    total_risk += severity  # Negative = safety point; no multiplier
                else:
                    total_risk += severity * time_multiplier  # Night multiplier applied
                    
                unsafe_pins.append({
                    "lat": float(crime['latitude']),
                    "lng": float(crime['longitude']),
                    "type": crime['type'],
                    "desc": crime['description'],
                    "severity": int(severity)
                })
    
    # Remove duplicates
    unique_pins = [dict(t) for t in {tuple(d.items()) for d in unsafe_pins}]
    
    # Safety score: 100 = perfect, 0 = very dangerous
    safety_score = max(0, min(100, 100 - (total_risk * 2)))
    
    return round(safety_score, 2), unique_pins


# ============================================================================
# FEATURE 1: TRIPLE-ROUTE NAVIGATION
# ============================================================================

def get_multiple_routes(origin_coords, dest_coords, num_alternatives=3):
    """Fetch multiple alternative routes from OSRM"""
    origin = f"{origin_coords[0]},{origin_coords[1]}"
    dest = f"{dest_coords[0]},{dest_coords[1]}"
    
    # OSRM supports alternatives parameter
    osrm_url = f"http://router.project-osrm.org/route/v1/walking/{origin};{dest}?overview=full&geometries=geojson&alternatives={num_alternatives}"
    
    try:
        r = requests.get(osrm_url, timeout=5).json()
        if r.get('code') != 'Ok':
            return None
        return r.get('routes', [])
    except Exception:
        return None

def generate_safety_narrative(score, pins, category, multiplier_label):
    """Generate a human-readable AI safety summary from the crime data"""
    if not pins:
        if score >= 85:
            return f"✅ Clear path detected. No crime incidents within 300m. {multiplier_label}."
        else:
            return f"✅ Route appears safe with minimal crime data nearby. {multiplier_label}."

    crime_types = {}
    for pin in pins:
        t = pin.get('type', 'Unknown')
        if t not in crime_types:
            crime_types[t] = 0
        crime_types[t] += 1

    top_crime = max(crime_types, key=crime_types.get)
    count = len(pins)
    
    if category == 'risky':
        return f"⚠️ HIGH RISK: {count} incidents near route, primarily {top_crime}. Avoid if possible. {multiplier_label}."
    elif category == 'moderate':
        return f"⚠️ {count} flagged zones detected, mainly {top_crime}. Stay alert and use well-lit paths. {multiplier_label}."
    else:
        return f"✅ Generally safe with {count} minor zone caution(s) — mainly {top_crime}. {multiplier_label}."


def classify_route_safety(score):
    """Classify route as Safe, Moderate, or Risky — using CSS theme colors"""
    if score >= 70:
        return "safe", "#10B981", "Safest Route ✓"
    elif score >= 40:
        return "moderate", "#F59E0B", "Moderate Route ⚠"
    else:
        return "risk", "#EF4444", "Risky Route ✗"

# ============================================================================
# FEATURE 2: HEATMAP DATA
# ============================================================================

def get_heatmap_data(crime_df):
    """Generate heatmap data points with intensity based on severity"""
    heatmap_points = []
    
    for _, crime in crime_df.iterrows():
        severity = crime['severity']
        
        # Only include danger zones (positive severity)
        if severity > 0:
            # Normalize intensity: severity 10 = intensity 1.0
            intensity = min(severity / 10, 1.0)
            
            heatmap_points.append({
                "lat": float(crime['latitude']),
                "lng": float(crime['longitude']),
                "intensity": intensity
            })
    
    return heatmap_points


# ============================================================================
# FEATURE 3: SAFE-HAVEN LOCATOR
# ============================================================================

def find_nearest_safe_havens(lat, lng, crime_df, limit=3):
    """Find nearest police stations, CCTV zones, and hospitals"""
    safe_havens = []
    
    # Filter for safety points (negative severity)
    safety_df = crime_df[crime_df['severity'] < 0].copy()
    
    for _, point in safety_df.iterrows():
        distance = haversine(lat, lng, float(point['latitude']), float(point['longitude']))
        
        safe_havens.append({
            "type": point['type'],
            "lat": float(point['latitude']),
            "lng": float(point['longitude']),
            "distance": round(distance, 2),
            "description": point['description']
        })
    
    # Sort by distance and return top N
    safe_havens.sort(key=lambda x: x['distance'])
    return safe_havens[:limit]


# ============================================================================
# FEATURE 4: SOS CONTEXT DATA
# ============================================================================

def get_sos_context(lat, lng, crime_df, route_geometry=None):
    """Generate SOS alert context with nearby dangers and route info"""
    nearby_dangers = []
    
    # Find all high-severity incidents within 500m
    danger_df = crime_df[crime_df['severity'] >= 7].copy()
    
    for _, danger in danger_df.iterrows():
        distance = haversine(lat, lng, float(danger['latitude']), float(danger['longitude']))
        
        if distance < 0.5:  # Within 500m
            nearby_dangers.append({
                "type": danger['type'],
                "severity": int(danger['severity']),
                "distance": round(distance * 1000, 0),  # in meters
                "description": danger['description']
            })
    
    # Sort by severity and distance
    nearby_dangers.sort(key=lambda x: (-x['severity'], x['distance']))
    
    return {
        "user_location": {"lat": lat, "lng": lng},
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nearby_dangers": nearby_dangers[:5],  # Top 5 closest high-risk areas
        "safe_havens": find_nearest_safe_havens(lat, lng, crime_df, limit=2)
    }


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route("/")
def index():
    """Main page - load map with initial crime pins"""
    try:
        df = get_crime_df()
        all_pins = df.to_dict(orient='records')
        return render_template("index.html", initial_pins=all_pins)
    except Exception as e:
        return f"<h3>System Error: Could not initialize map data.</h3><p>{str(e)}</p>", 500

@app.route("/get_triple_routes", methods=["POST"])
def get_triple_routes():
    """
    FEATURE 1: Return 3 alternative routes ranked by safety
    Request: {origin: "place name", destination: "place name"}
    Response: {routes: [{geometry, safety_score, category, pins, distance}...]}
    """
    data = request.json
    origin_name = data.get('origin')
    dest_name = data.get('destination')
    
    # Convert names to coordinates
    origin_coords = get_coordinates(origin_name)
    dest_coords = get_coordinates(dest_name)
    
    if not origin_coords or not dest_coords:
        return jsonify({"error": "Could not find one or both locations. Try being more specific."}), 400
    
    # Get multiple routes from OSRM
    routes = get_multiple_routes(origin_coords, dest_coords, num_alternatives=3)
    
    if not routes:
        return jsonify({"error": "No routes found between these locations."}), 400
    
    try:
        df = get_crime_df()
        # Get current time multiplier
        multiplier, multiplier_label = get_time_risk_multiplier()
        
        # Score each route with time-aware risk
        scored_routes = []
        for route in routes:
            score, pins = calculate_safety(route['geometry']['coordinates'], df, multiplier)
            category, color, label = classify_route_safety(score)
            narrative = generate_safety_narrative(score, pins, category, multiplier_label)
            
            scored_routes.append({
                "geometry": route['geometry'],
                "safety_score": score,
                "category": category,
                "color": color,
                "label": label,
                "pins": pins,
                "distance": f"{round(route['distance']/1000, 2)} km",
                "duration": f"{round(route['duration']/60, 0)} min",
                "narrative": narrative,
                "time_label": multiplier_label
            })
        
        # Sort by safety score (descending)
        scored_routes.sort(key=lambda x: x['safety_score'], reverse=True)
        
        return jsonify({"routes": scored_routes, "time_context": multiplier_label})
    except Exception as e:
        return jsonify({"error": "Internal route processing error", "details": str(e)}), 500


@app.route("/get_heatmap", methods=["GET"])
def get_heatmap():
    """
    FEATURE 2: Return heatmap data for crime visualization
    Response: {heatmap_points: [{lat, lng, intensity}...]}
    """
    try:
        df = get_crime_df()
        heatmap_points = get_heatmap_data(df)
        return jsonify({"heatmap_points": heatmap_points})
    except Exception as e:
        return jsonify({"error": "Failed to generate heatmap", "details": str(e)}), 500


@app.route("/find_safe_havens", methods=["POST"])
def find_safe_havens():
    """
    FEATURE 3: Find nearest police stations and safe zones
    Request: {lat: float, lng: float}
    Response: {safe_havens: [{type, lat, lng, distance, description}...]}
    """
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not lat or not lng:
        return jsonify({"error": "Coordinates required"}), 400
    
    try:
        df = get_crime_df()
        safe_havens = find_nearest_safe_havens(float(lat), float(lng), df, limit=5)
        return jsonify({"safe_havens": safe_havens})
    except Exception as e:
        return jsonify({"error": "Failed to locate safe havens", "details": str(e)}), 500


@app.route("/get_radar_scan", methods=["POST"])
def get_radar_scan():
    """
    FEATURE 5: Contextual Safety Radar
    Request: {lat: float, lng: float}
    Response: {safety_score, nearby_crimes, safe_havens}
    """
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')

    if not lat or not lng:
        return jsonify({"error": "Coordinates required"}), 400

    try:
        df = get_crime_df()
        
        # 1. Calculate local safety score (within 1km radius)
        total_risk = 0
        nearby_crimes = []
        
        for _, crime in df.iterrows():
            distance = haversine(float(lat), float(lng), float(crime['latitude']), float(crime['longitude']))
            if distance < 1.0: # 1km radar radius
                severity = crime['severity']
                if severity > 0:
                    total_risk += severity
                    nearby_crimes.append({
                        "lat": float(crime['latitude']),
                        "lng": float(crime['longitude']),
                        "type": crime['type'],
                        "distance": round(distance * 1000, 0),
                        "severity": int(severity)
                    })

        # Sort by closest and take top 5
        nearby_crimes.sort(key=lambda x: x['distance'])
        nearby_crimes = nearby_crimes[:5]

        # Calculate 0-100 score based on density of risk nearby
        safety_score = max(0, min(100, 100 - (total_risk * 1.5)))
        
        # 2. Get nearest safe havens
        safe_havens = find_nearest_safe_havens(float(lat), float(lng), df, limit=2)

        return jsonify({
            "safety_score": round(safety_score, 1),
            "nearby_crimes": len(nearby_crimes),
            "recent_incidents": nearby_crimes,
            "safe_havens": safe_havens
        })
    except Exception as e:
        return jsonify({"error": "Radar scan failed", "details": str(e)}), 500


@app.route("/send_sos", methods=["POST"])
def send_sos():
    """
    FEATURE 4: Generate SOS alert context
    Request: {lat: float, lng: float, route_geometry: optional}
    Response: {sos_context: {user_location, timestamp, nearby_dangers, safe_havens}}
    """
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    route_geometry = data.get('route_geometry')
    
    if not lat or not lng:
        return jsonify({"error": "Location required"}), 400
    
    try:
        df = get_crime_df()
        sos_context = get_sos_context(float(lat), float(lng), df, route_geometry)
        return jsonify({"sos_context": sos_context})
    except Exception as e:
        return jsonify({"error": "Failed to generate SOS context", "details": str(e)}), 500




@app.route("/get_stats", methods=["GET"])
def get_stats():
    """Return live dataset statistics for the UI sidebar header"""
    try:
        df = get_crime_df()
        _, time_label = get_time_risk_multiplier()
        return jsonify({
            "total_incidents": int((df["severity"] > 0).sum()),
            "high_severity": int((df["severity"] >= 7).sum()),
            "safe_zones": int((df["severity"] < 0).sum()),
            "time_context": time_label
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)