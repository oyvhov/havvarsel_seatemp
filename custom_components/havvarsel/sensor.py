import logging
import requests
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Havvarsel temperatureprojection endpoint format:
      /temperatureprojection/{LON}/{LAT}
    We'll invert user inputs here.
    """
    return (
        "https://api.havvarsel.no/apis/duapi/havvarsel/v2/temperatureprojection/"
        f"{longitude}/{latitude}"
    )

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Havvarsel sensor."""
    lat = config_entry.data.get(CONF_LATITUDE)
    lon = config_entry.data.get(CONF_LONGITUDE)

    sensor = HavvarselSeaTemperatureSensor(lat, lon)
    async_add_entities([sensor], update_before_add=True)


class HavvarselSeaTemperatureSensor(Entity):
    """Representation of a Havvarsel sea temperature sensor."""

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
        # E.g. havvarsel_sea_temp_60.39_5.32
        return f"havvarsel_sea_temp_{self._latitude}_{self._longitude}"

    @property
    def state(self):
        """Return the current temperature."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return self._attributes

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Fetch JSON data from Havvarsel temperatureprojection endpoint."""
        url = build_api_url(self._latitude, self._longitude)
        headers = {"Accept": "application/json"}

        _LOGGER.debug("Requesting Havvarsel data from: %s", url)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                _LOGGER.error("Havvarsel error %s: %s", resp.status_code, resp.text)
                return

            data = resp.json()
            _LOGGER.debug("Havvarsel response: %s", data)

            # The JSON structure is:
            # {
            #   "variables": [
            #     {
            #       "variableName": "temperature",
            #       "dimensions": [...],
            #       "data": [
            #         { "value": 8.17, "rawTime": 1.7400888E12 },
            #         ...
            #       ],
            #       "metadata": [...]
            #     }
            #   ],
            #   "queryPoint": { ... },
            #   "closestGridPoint": { ... },
            #   "closestGridPointWithData": { ... }
            # }

            variables = data.get("variables", [])
            if not variables:
                _LOGGER.warning("No 'variables' array in Havvarsel response.")
                return

            # Grab the first variable object:
            temperature_var = variables[0]

            # Get the data array of temperature/time values
            data_list = temperature_var.get("data", [])
            if not data_list:
                _LOGGER.warning("No 'data' array in Havvarsel 'variables[0]'.")
                return

            # Let's just take the first data point as "current" temperature
            first_point = data_list[0]
            temperature = first_point.get("value")
            raw_time = first_point.get("rawTime")  # note: "rawTime" instead of "raw_time"

            if temperature is not None:
                self._state = round(float(temperature), 2)
            else:
                self._state = None

            # Convert raw_time (epoch ms) to a datetime
            if raw_time is not None:
                try:
                    dt = datetime.utcfromtimestamp(float(raw_time) / 1000.0)
                    self._attributes["forecast_time"] = dt.isoformat()
                except ValueError:
                    self._attributes["forecast_time"] = str(raw_time)
            else:
                self._attributes["forecast_time"] = None

            # Optionally store other info (metadata, etc.)
            self._attributes["latitude"] = self._latitude
            self._attributes["longitude"] = self._longitude

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Exception while fetching Havvarsel data: %s", err)
