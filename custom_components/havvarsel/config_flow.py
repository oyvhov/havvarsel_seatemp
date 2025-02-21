import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)

class HavvarselConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Havvarsel."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate latitude and longitude if necessary
            # For simplicity, we'll accept any strings or floats:
            lat = user_input.get(CONF_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE)

            # If you want to ensure they're valid floats:
            try:
                float(lat)
                float(lon)
            except ValueError:
                errors["base"] = "invalid_coordinates"
            else:
                return self.async_create_entry(
                    title=f"Havvarsel ({lat}, {lon})",
                    data={
                        CONF_LATITUDE: lat,
                        CONF_LONGITUDE: lon
                    }
                )

        # Show the form if there's no user input or there's an error
        data_schema = vol.Schema(
            {
                vol.Required(CONF_LATITUDE): cv.string,
                vol.Required(CONF_LONGITUDE): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HavvarselOptionsFlowHandler(config_entry)


class HavvarselOptionsFlowHandler(config_entries.OptionsFlow):
    """If you want to allow updating options after install."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE,
                    default=self.config_entry.data.get(CONF_LATITUDE),
                ): cv.string,
                vol.Required(
                    CONF_LONGITUDE,
                    default=self.config_entry.data.get(CONF_LONGITUDE),
                ): cv.string,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
