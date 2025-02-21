import logging
import requests
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util.dt import now as ha_now  # homeassistant.util.dt.now()

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Havvarsel temperatureprojection endpoint format:
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

    sensor = HavvarselSeaTemperatureSensor(lat, lon)
    async_add_entities([sensor], update_before_add=True)

class HavvarselSeaTemperatureSensor(Entity):
    """
    A sensor that:
    - Fetches Havvarsel temperature data (JSON).
    - Builds a list of hourly blocks in the attribute 'raw_today'.
    - Sets the sensor's state to the block matching 'current hour'.
    """

    def __init__(self, latitude, longitude):
        self._latitude = latitude
        self._longitude = longitude
        self._state = None
        self._attributes = {}
        self._name = "Sea Temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID based on lat/lon."""
        return f"havvarsel_sea_temp_{self._latitude}_{self._longitude}_{self.entry_id}"

    @property
    def state(self):
        """Return the current hour's temperature, if found."""
        return self._state

    @property
    def extra_state_attributes(self):
        """
        Return additional attributes, including a list of
        all forecast blocks under 'raw_today'.
        """
        return self._attributes

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Fetch JSON data, build the list of blocks, and find the current hour's temperature."""
        url = build_api_url(self._latitude, self._longitude)
        headers = {"Accept": "application/json"}

        _LOGGER.debug("Requesting Havvarsel data from: %s", url)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            _LOGGER.debug("Havvarsel status code: %s", resp.status_code)
            _LOGGER.debug("Havvarsel raw response: %s", resp.text)

            if resp.status_code != 200:
                _LOGGER.error("Havvarsel error %s: %s", resp.status_code, resp.text)
                return

            data = resp.json()
            _LOGGER.debug("Havvarsel parsed JSON: %s", data)

            # The JSON structure typically looks like:
            # {
            #   "variables": [
            #     {
            #       "variableName": "temperature",
            #       "data": [
            #         {"value": 8.17, "rawTime": 1.7400888E12},
            #         ...
            #       ],
            #       ...
            #     }
            #   ],
            #   ...
            # }

            variables = data.get("variables", [])
            if not variables:
                _LOGGER.warning("No 'variables' array in response, cannot parse.")
                return

            # Usually temperature data is in the first element
            temperature_var = variables[0]
            data_list = temperature_var.get("data", [])
            if not data_list:
                _LOGGER.warning("No 'data' array in first variable.")
                return

            # Build a list of forecast blocks
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

            # Store the entire forecast in an attribute
            self._attributes["raw_today"] = raw_today_list

            # We'll attempt to find the block matching "current hour".
            now_ha = ha_now()  # typically local time in modern HA
            _LOGGER.debug("Home Assistant current time: %s", now_ha)

            current_temp = None

            # Check each block to see if 'now' is within [start, end)
            for block in raw_today_list:
                start_dt = datetime.fromisoformat(block["start"])
                end_dt = datetime.fromisoformat(block["end"])
                _LOGGER.debug(
                    "Comparing block: start=%s, end=%s, value=%s",
                    start_dt, end_dt, block["value"]
                )

                # If your forecast times are in UTC, but now_ha is local, they might never match.
                # Option A: convert start_dt and end_dt to local time
                # Option B: convert now_ha to UTC
                # We'll do Option B here for clarity:
                now_utc = datetime.utcnow()
                if start_dt <= now_utc < end_dt:
                    current_temp = block["value"]
                    _LOGGER.debug("Found matching block => %s", current_temp)
                    break

            if current_temp is not None:
                self._state = current_temp
            else:
                # No matching block => show None
                _LOGGER.debug("No block matched the current time.")
                self._state = None

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Exception while fetching Havvarsel data: %s", err)
