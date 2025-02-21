import logging
import requests
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import Throttle
from homeassistant.util.dt import now as ha_now

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Havvarsel temperatureprojection-endepunkt:
      /temperatureprojection/{LON}/{LAT}
    Vi inverterer lat/lon for å matche endepunktet.
    """
    return (
        "https://api.havvarsel.no/apis/duapi/havvarsel/v2/temperatureprojection/"
        f"{longitude}/{latitude}"
    )

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Sett opp Havvarsel-sensoren via config entry."""
    lat = config_entry.data.get(CONF_LATITUDE)
    lon = config_entry.data.get(CONF_LONGITUDE)

    sensor = HavvarselSeaTemperatureSensor(lat, lon)
    async_add_entities([sensor], update_before_add=True)

class HavvarselSeaTemperatureSensor(SensorEntity):
    """
    En sensor som henter temperatur fra Havvarsel, 
    lagrer hele forecast-listen i attributter,
    og setter state til nåværende times temperatur.
    """

    def __init__(self, latitude, longitude):
        self._latitude = latitude
        self._longitude = longitude
        self._attr_name = "Sea Temperature"
        self._attr_unique_id = f"havvarsel_sea_temp_{latitude}_{longitude}"

        # Bruker None inntil vi faktisk får data
        self._state = None
        self._attributes = {}

    @property
    def native_value(self):
        """Returner aktuell verdi (nåværende times temperatur)."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Returner tilleggsegenskaper, f.eks. full forecast-liste."""
        return self._attributes

    @property
    def device_class(self):
        """Angi at dette er en temperatursensor."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        """Angi måleenhet (°C)."""
        return TEMP_CELSIUS

    @property
    def icon(self):
        """Sett standardikon til 'mdi:coolant-temperature'."""
        return "mdi:coolant-temperature"

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Hent JSON-data, bygg lister og finn temperatur for 'nåværende time'."""
        url = build_api_url(self._latitude, self._longitude)
        headers = {"Accept": "application/json"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                _LOGGER.error("Feil fra Havvarsel %s: %s", resp.status_code, resp.text)
                return

            data = resp.json()
            variables = data.get("variables", [])
            if not variables:
                _LOGGER.warning("Fant ingen 'variables' i responsen.")
                return

            temperature_var = variables[0]
            data_list = temperature_var.get("data", [])
            if not data_list:
                _LOGGER.warning("Fant ingen 'data' i første 'variables'.")
                return

            # Bygg en liste av 1-times intervaller
            raw_today_list = []
            for point in data_list:
                value = point.get("value")
                raw_time = point.get("rawTime")  # epoch ms
                if value is not None and raw_time is not None:
                    dt_start = datetime.utcfromtimestamp(raw_time / 1000.0)
                    dt_end = dt_start + timedelta(hours=1)
                    block = {
                        "start": dt_start.isoformat(),
                        "end": dt_end.isoformat(),
                        "value": round(value, 2),
                    }
                    raw_today_list.append(block)

            # Lagre hele forecasten i attributt
            self._attributes["raw_today"] = raw_today_list

            # Finn blokken som matcher nåværende time
            now_ha = ha_now()
            current_temp = None

            # Alternativt kan vi konvertere now_ha til UTC om data er i UTC
            now_utc = datetime.utcnow()

            for block in raw_today_list:
                start_dt = datetime.fromisoformat(block["start"])
                end_dt = datetime.fromisoformat(block["end"])
                if start_dt <= now_utc < end_dt:
                    current_temp = block["value"]
                    break

            self._state = current_temp

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Klarte ikke å hente Havvarsel-data: %s", err)
