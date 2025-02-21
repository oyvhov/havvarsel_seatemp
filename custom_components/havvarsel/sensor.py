import logging
from datetime import datetime, timedelta

import requests
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=UPDATE_INTERVAL)

def build_api_url(latitude: str, longitude: str) -> str:
    """
    Construct the Havvarsel API URL.
    Adjust this based on the actual API endpoints/parameters you need.
    """
    return (
        f"https://api.havvarsel.no/apis/duapi/havvarsel/v2/weather"
        f"?lat={latitude}&lon={longitude}"
    )

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Havvarsel sensor entity."""
    latitude = config_entry.data.get(CONF_LATITUDE)
    longitude = config_entry.data.get(CONF_LONGITUDE)

    sensor = HavvarselSeaTemperatureSensor(latitude, longitude)
    async_add_entities([sensor], update_before_add=True)


class HavvarselSeaTemperatureSensor(Entity):
    """Representation of a Havvarsel sea temperature sensor."""

    def __init__(self, latitude, longitude):
        """Initialize the sensor."""
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
        """Return a unique_id for this entity (optional but recommended)."""
        return f"havvarsel_sea_temp_{self._latitude}_{self._longitude}"

    @property
    def state(self):
        """Return the current temperature."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional attributes, if any."""
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """
        Fetch the latest data from the Havvarsel API.
        This is a synchronous method. 
        For advanced usage, consider the DataUpdateCoordinator pattern or asynchronous methods.
        """
        url = build_api_url(self._latitude, self._longitude)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # TODO: Adjust this parsing based on the actual Havvarsel API JSON structure.
                # This is just an example to show how you might extract sea temperature.
                # Example placeholders:
                # "seaTemperature": 5.2

                sea_temp = None
                if "seaTemperature" in data:
                    sea_temp = data["seaTemperature"]

                self._state = sea_temp
                self._attributes["last_update"] = datetime.now().isoformat()
            else:
                _LOGGER.error("Error response from Havvarsel API: %s", response.text)

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Request error: %s", err)
