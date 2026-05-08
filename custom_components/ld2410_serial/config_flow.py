import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from .const import (
    DOMAIN, 
    CONF_SERIAL_PORT, 
    CONF_BAUD_RATE, 
    DEFAULT_BAUD_RATE,
    CONF_MAX_MOVING,
    CONF_MAX_STATIC,
    CONF_TIMEOUT
)

class LD2410SerialConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LD2410 Serial."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LD2410OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # You could add validation here (e.g. check if serial port exists)
            return self.async_create_entry(title=f"LD2410 ({user_input[CONF_SERIAL_PORT]})", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_SERIAL_PORT, default="/dev/ttyS1"): str,
            vol.Required(CONF_BAUD_RATE, default=DEFAULT_BAUD_RATE): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

class LD2410OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for LD2410 Serial."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        
        data_schema = vol.Schema({
            vol.Required(CONF_MAX_MOVING, default=options.get(CONF_MAX_MOVING, 4)): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Required(CONF_MAX_STATIC, default=options.get(CONF_MAX_STATIC, 4)): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Required(CONF_TIMEOUT, default=options.get(CONF_TIMEOUT, 5)): vol.All(vol.Coerce(int), vol.Range(min=1, max=3600)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema
        )
