from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, UPDATE_SIGNAL, CONF_SERIAL_PORT
import os

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    async_add_entities([
        LD2410PresenceSensor(hass, entry),
        LD2410MovingTargetSensor(hass, entry),
        LD2410StaticTargetSensor(hass, entry)
    ])

class LD2410BaseBinarySensor(BinarySensorEntity):
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_has_entity_name = True

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        port = self.entry.data.get(CONF_SERIAL_PORT, "")
        port_name = os.path.basename(port) if port else "Radar"
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=f"LD2410 {port_name}",
            manufacturer="Hi-Link",
            model="LD2410"
        )

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"{UPDATE_SIGNAL}_{self.entry.entry_id}", self._handle_update)
        )

    def _handle_update(self):
        self.schedule_update_ha_state()

class LD2410PresenceSensor(LD2410BaseBinarySensor):
    _attr_name = "Presence"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_presence"

    @property
    def is_on(self):
        latest = self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {})
        return latest.get("target_state", 0x00) != 0x00

class LD2410MovingTargetSensor(LD2410BaseBinarySensor):
    _attr_name = "Moving Target"
    _attr_device_class = BinarySensorDeviceClass.MOTION

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_moving_target"

    @property
    def is_on(self):
        latest = self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {})
        return latest.get("target_state", 0x00) in (0x01, 0x03)

class LD2410StaticTargetSensor(LD2410BaseBinarySensor):
    _attr_name = "Static Target"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_static_target"

    @property
    def is_on(self):
        latest = self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {})
        return latest.get("target_state", 0x00) in (0x02, 0x03)
