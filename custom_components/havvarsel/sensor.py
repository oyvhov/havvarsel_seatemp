import logging
import requests
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util.dt import now as ha_now

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Havvarsel temperature projection endpoint format:
    /temperatureprojection/{LON}/{LAT}
    We'll invert lat/lon here because the user inputs lat/long in the normal order.
    """
    return (
        "https://api.havvarsel.no/apis/duapi/havvarsel/v2/temperatureprojection/"
        f"{longitude}/{latitude}"
    )

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Havvarsel sensor via config entry."""
    lat = config_entry.data.get(CONF_LATITUDE)
    lon = config_entry.data.get(CONF_LONGITUDE)
    name = config_entry.data.get(CONF_NAME, "Sea Temperature Sensor")  # Use custom name

    sensor = HavvarselSeaTemperatureSensor(name, lat, lon)
    async_add_entities([sensor], update_before_add=True)

class HavvarselSeaTemperatureSensor(Entity):
    """
    A sensor that fetches Havvarsel temperature data and updates its state.
    """

    def __init__(self, name, latitude, longitude):
        self._name = name
        self._latitude = latitude
        self._longitude = longitude
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the user-defined name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID based on lat/lon."""
        return f"havvarsel_sea_temp_{self._latitude}_{self._longitude}"

    @property
    def state(self):
        """Return the current hour's temperature, if found."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return self._attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement as Celsius."""
        return "°C"

    @property
    def device_class(self):
        """Return the device class as temperature."""
        return "temperature"

    @property
    def state_class(self):
        """Return the state class as measurement."""
        return "measurement"

    @property
    def icon(self):
        """Return an appropriate icon for sea temperature."""
        return "mdi:thermometer-water"

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Fetch JSON data, build the list of blocks, and find the current hour's temperature."""
        url = build_api_url(self._latitude, self._longitude)
        headers = {"Accept": "application/json"}

        _LOGGER.debug("Requesting Havvarsel data from: %s", url)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            variables = data.get("variables", [])
            if not variables:
                _LOGGER.warning("No 'variables' array in response, cannot parse.")
                return

            temperature_var = variables[0]
            data_list = temperature_var.get("data", [])
            if not data_list:
                _LOGGER.warning("No 'data' array in first variable.")
                return

            raw_today_list = []
            for point in data_list:
                value = point.get("value")
                raw_time = point.get("rawTime")  # epoch ms
                if value is not None and raw_time is not None:
                    dt_start = datetime.utcfromtimestamp(raw_time / 1000.0)
                    dt_end = dt_start + timedelta(hours=1)  # assume each step is 1 hour
                    block = {
                        "start": dt_start.isoformat(),
                        "end": dt_end.isoformat(),
                        "value": round(value, 2),
                    }
                    raw_today_list.append(block)

            self._attributes["raw_today"] = raw_today_list

            now_utc = datetime.utcnow()
            current_temp = None

            for block in raw_today_list:
                start_dt = datetime.fromisoformat(block["start"])
                end_dt = datetime.fromisoformat(block["end"])

                if start_dt <= now_utc < end_dt:
                    current_temp = block["value"]
                    break

            self._state = current_temp if current_temp is not None else None

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Exception while fetching Havvarsel data: %s", err)
