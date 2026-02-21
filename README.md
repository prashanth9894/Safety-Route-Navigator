# 🛡️ SafeRoute: Safety route Navigator

**SafeRoute AI** is an advanced AI-powered navigation platform designed to prioritize personal safety. Unlike traditional maps that focus solely on the fastest route, SafeRoute AI analyzes real-time and historical crime data to suggest the **safest** possible paths for travelers.

![SafeRoute AI Banner](https://img.shields.io/badge/Safety-First-green?style=for-the-badge&logo=shield)
![Status](https://img.shields.io/badge/Status-Hackathon--Ready-blue?style=for-the-badge)

## 🚀 Key Features

### 🛣️ Triple-Route Navigation
View three alternative routes ranked by safety. Each route is analyzed for proximity to known crime incidents, giving you the power to choose between speed and security.

### 🕒 Time-Aware Risk Assessment
Crime patterns change at night. Our algorithm applies a dynamic "Night Risk Multiplier" based on NCRB-informed data (peaking between 10 PM and 4 AM) to adjust safety scores in real-time.

### 🗺️ Dynamic Crime Heatmap
Visualize high-risk zones through an interactive heatmap. See where incidents are clustered and stay informed about your surroundings.

### 🛡️ Safe-Haven Locator
Instantly find the nearest "Safe Zones" including:
- 🚓 Police Stations
- 📹 High-Density CCTV Areas
- 🏥 24/7 Hospitals

### 📡 Contextual Safety Radar
Perform a "Radar Scan" of your current location to see a safety score (0-100) and a list of the 5 closest security flags or safe havens.

### 🆘 Intelligent SOS Context
In emergencies, generate instant SOS context that captures your exact coordinates, nearby dangers, and the fastest route to the nearest safe haven for emergency responders.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Data Processing:** Pandas, Haversine Algorithm
- **Mapping & Routing:** Leaflet.js, OSRM (Open Source Routing Machine), OpenStreetMap (Nominatim)
- **UI/UX:** Modern CSS with Glassmorphism and vibrant safety-themed color palettes.

## 📥 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/prashanth9894/Smart-route-safety-navigator.git
   cd Smart-route-safety-navigator
   ```

2. **Install dependencies:**
   ```bash
   pip install flask pandas requests
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the App:**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📊 Data Insights

The system currently leverages detailed crime history data from **Tamil Nadu**, focusing on incident types such as street theft, harassment, and poorly lit zones to provide highly localized safety insights.

## 💡 How it Works

1. **Route Sampling:** The system samples coordinates along every 5th point of a generated route.
2. **Proximity Analysis:** It checks for crime incidents within a **300m radius** of each sampled point.
3. **Safety Scoring:** A base score of 100 is adjusted based on crime severity and the **Time-of-Day Multiplier**.
4. **Narrative Generation:** AI-driven summaries explain *why* a route is classified as Safe, Moderate, or Risky.

---
*Built for the ultimate peace of mind while traveling.*
