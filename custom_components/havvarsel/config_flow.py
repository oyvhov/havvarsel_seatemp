import logging
import voluptuous as vol

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)


class HavvarselConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Havvarsel Sea Temperature."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Basic validation for lat/lon
            try:
                float(user_input[CONF_LATITUDE])
                float(user_input[CONF_LONGITUDE])
            except ValueError:
                errors["base"] = "invalid_coordinates"
            else:
                # If valid, create the config entry
                return self.async_create_entry(
                    title=f"Havvarsel Sea Temp ({user_input[CONF_LATITUDE]}, {user_input[CONF_LONGITUDE]})",
                    data=user_input
                )

        data_schema = vol.Schema({
            vol.Required(CONF_LATITUDE): cv.string,
            vol.Required(CONF_LONGITUDE): cv.string,
        })

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
    """Handle options (edit lat/lon after initial setup)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Required(
                CONF_LATITUDE,
                default=self.config_entry.data.get(CONF_LATITUDE)
            ): cv.string,
            vol.Required(
                CONF_LONGITUDE,
                default=self.config_entry.data.get(CONF_LONGITUDE)
            ): cv.string,
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)
