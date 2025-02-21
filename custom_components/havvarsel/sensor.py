import logging
import requests
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util.dt import now as ha_now  # or import as_local, etc.

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Havvarsel temperatureprojection endpoint format:
      /temperatureprojection/{LON}/{LAT}
    We'll invert lat/lon here.
    """
    return (
        "https://api.havvarsel.no/apis/duapi/havvarsel/v2/temperatureprojection/"
        f"{longitude}/{latitude}"
    )

async def async_setup_entry(hass, config_entry, async_add_entities):
    lat = config_entry.data.get(CONF_LATITUDE)
    lon = config_entry.data.get(CONF_LONGITUDE)

    sensor = HavvarselSeaTemperatureSensor(lat, lon)
    async_add_entities([sensor], update_before_add=True)


class HavvarselSeaTemperatureSensor(Entity):
    """Representation of a Havvarsel sea temperature sensor, with a full forecast attribute."""

    def __init__(self, latitude, longitude):
        self._latitude = latitude
        self._longitude = longitude
        self._state = None
        self._attributes = {}
        self._name = "Sea Temperature"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"havvarsel_sea_temp_{self._latitude}_{self._longitude}"

    @property
    def state(self):
        """The temperature for the **current hour**."""
        return self._state

    @property
    def extra_state_attributes(self):
        """All forecast data (raw_today) plus any other info."""
        return self._attributes

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Fetch JSON data, build a list of 1-hour blocks, and set state to the 'current hour' temp."""
        url = build_api_url(self._latitude, self._longitude)
        headers = {"Accept": "application/json"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                _LOGGER.error("Havvarsel error %s: %s", resp.status_code, resp.text)
                return

            data = resp.json()
            variables = data.get("variables", [])
            if not variables:
                _LOGGER.warning("No 'variables' array in response.")
                return

            # The temperature data is typically in the first object
            temperature_var = variables[0]
            data_list = temperature_var.get("data", [])
            if not data_list:
                _LOGGER.warning("No 'data' array in temperature_var.")
                return

            raw_today_list = []
            for point in data_list:
                value = point.get("value")
                raw_time = point.get("rawTime")  # epoch ms
                if value is not None and raw_time is not None:
                    # Convert epoch ms to a Python datetime (UTC)
                    dt_start = datetime.utcfromtimestamp(raw_time / 1000.0)
                    dt_end = dt_start + timedelta(hours=1)  # each forecast block is 1 hour

                    raw_today_list.append({
                        "start": dt_start.isoformat(),
                        "end": dt_end.isoformat(),
                        "value": round(value, 2),
                    })

            # Store the entire forecast in an attribute
            self._attributes["raw_today"] = raw_today_list

            # Find the block that includes "now"
            # Use Home Assistant's 'now()' (UTC or local—depends on your preference).
            now_ha = ha_now()  # Typically returns local time with timezone in modern HA
  
