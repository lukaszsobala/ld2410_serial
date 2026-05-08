import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_SERIAL_PORT, CONF_BAUD_RATE, DEFAULT_BAUD_RATE

class LD2410SerialConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LD2410 Serial."""

    VERSION = 1

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
