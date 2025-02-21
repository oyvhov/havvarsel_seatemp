import logging
import requests
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import (
    DOMAIN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Build the Havvarsel temperatureprojection URL. 
    NOTE: The endpoint expects /temperatureprojection/{LONGITUDE}/{LATITUDE}.
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
        return f"havvarsel_sea_temp_{self._latitude}_{self._longitude}"

    @property
    def state(self):
        """Return the current temperature."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return self._attributes

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Fetch JSON data from Havvarsel temperatureprojection endpoint."""
        url = build_api_url(self._latitude, self._longitude)
        headers = {"Accept": "application/json"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                _LOGGER.error(
                    "Havvarsel returned status %s: %s",
                    resp.status_code,
                    resp.text
                )
                return

            data = resp.json()
            # The JSON should have a structure like:
            # {
            #   "projection": {
            #     "variables": {
            #       "variableName": "temperature",
            #       "data": [
            #         {
            #           "value": 8.17,
            #           "raw_time": 1.7400888E12
            #         },
            #         ...
            #       ]
            #       ...
            #     },
            #     ...
            #   }
            # }
            projection = data.get("projection", {})
            variables = projection.get("variables", {})
            data_list = variables.get("data", [])

            if not data_list:
                _LOGGER.warning("No 'data' array found in Havvarsel response.")
                return

            # For example, let's take the first data point
            first_point = data_list[0]
            temperature = first_point.get("value")
            raw_time = first_point.get("raw_time")

            if temperature is not None:
                self._state = round(float(temperature), 2)
            else:
                self._state = None

            if raw_time is not None:
                # raw_time is presumably epoch milliseconds
                try:
                    dt = datetime.utcfromtimestamp(float(raw_time) / 1000.0)
                    self._attributes["forecast_time"] = dt.isoformat()
                except ValueError:
                    self._attributes["forecast_time"] = str(raw_time)
            else:
                self._attributes["forecast_time"] = None

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error fetching Havvarsel data: %s", err)
