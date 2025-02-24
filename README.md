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
- **Repository URL**: `<your-repo-url>`  
- **Category**: `Integration`  
4. Search for **"Havvarsel"** in HACS and install.
5. Restart Home Assistant.

---

## ⚙️ Configuration

### **Adding the Integration**
1. Go to **Home Assistant → Settings → Devices & Services**.
2. Click **"Add Integration"** and search for **Havvarsel**.
3. Enter:
- **Sensor Name** (e.g., `"Bergen Sea Temp"`)
- **Latitude** (e.g., `61.356045`)
- **Longitude** (e.g., `5.18974`)

### **Example Entity**
After setup, you will get a **sensor entity**:

```yaml
sensor:
- platform: havvarsel
 name: "Sea Temperature"
 latitude: 61.356045
 longitude: 5.18974
