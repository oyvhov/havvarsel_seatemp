# 🌊 Havvarsel - Home Assistant Custom Integration

![Havvarsel](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)
![API](https://img.shields.io/badge/API-Havvarsel-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Maintained](https://img.shields.io/maintenance/yes/2025)  

## 📌 Overview
**Havvarsel** is a custom Home Assistant integration that fetches **sea temperature forecasts** from the **Havvarsel API** and provides real-time temperature data for a given location.

### 🌡 Features:
✅ Fetches **hourly** sea temperature predictions.  
✅ Displays **current hour's temperature** in Home Assistant.  
✅ Stores a **5-day forecast** in the `raw_today` attribute.  
✅ Provides **temperature history & trends** for automations.  
✅ **Works with multiple locations**.  

---

## 🔧 Installation

### 1️⃣ **Manual Installation**
1. Download this repository as a **ZIP file**.
2. Extract the `havvarsel` folder into:  
  /config/custom_components/havvarsel/
3. Restart Home Assistant.

### 2️⃣ **Installation via HACS (Recommended)**
1. Open **HACS** in Home Assistant.
2. Click **"Integrations" → "Custom Repositories"**.
3. Add:  
- **Repository URL**: `https://github.com/oyvhov/havvarsel_seatemp`  
- **Category**: `Integration`  
4. Search for **"Havvarsel"** in HACS and install.
5. Restart Home Assistant.

---

## ⚙️ Configuration

### **Adding the Integration**
1. Go to **Home Assistant → Settings → Devices & Services**.
2. Click **"Add Integration"** and search for **Havvarsel**.
3. Enter:

![image](https://github.com/user-attachments/assets/8d0768f0-1c24-4cb9-909b-b383059ae6c8)

- **Sensor Name** (e.g., `"Bergen Sea Temp"`)
- **Latitude** (e.g., `61.356045`)
- **Longitude** (e.g., `5.18974`)

### **Use**
Example of forecast with custom apex charts card (https://github.com/RomRider/apexcharts-card):


![image](https://github.com/user-attachments/assets/f6a9410c-ef5f-4d78-b9f1-a8ca536f2313)


```yaml
type: grid
cards:
  - type: heading
    heading_style: title
    grid_options:
      columns: 6
      rows: 1
    heading: Sjøtemperatur Bergen
    icon: mdi:coolant-temperature
  - type: custom:apexcharts-card
    graph_span: 120h
    experimental:
      color_threshold: false
    apex_config:
      chart:
        height: 240px
      grid:
        show: false
        borderColor: var(--blue)
    header:
      show: false
    span:
      start: day
    yaxis:
      - min: 0
        max: "|3|"
        decimals: 1
        show: true
    now:
      show: true
      label: "No"
      color: "#ffb581"
    all_series_config:
      float_precision: 2
    series:
      - entity: sensor.sea_temperature_bergen
        show:
          extremas: true
          in_header: false
          name_in_header: true
          in_chart: true
        name: Rivedal
        type: area
        curve: smooth
        extend_to: end
        stroke_width: 3
        opacity: 0.2
        color: "#90bfff"
        data_generator: |
          return entity.attributes.raw_today.map((start, index) => {
            return [new Date(start["start"]).getTime(), entity.attributes.raw_today[index]["value"]];
          });

