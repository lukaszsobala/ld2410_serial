from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, UPDATE_SIGNAL, CONF_SERIAL_PORT
import os

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    async_add_entities([
        LD2410MovingDistanceSensor(hass, entry),
        LD2410StaticDistanceSensor(hass, entry),
        LD2410DetectionDistanceSensor(hass, entry),
        LD2410MovingEnergySensor(hass, entry),
        LD2410StaticEnergySensor(hass, entry)
    ])

class LD2410BaseSensor(SensorEntity):
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

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

class LD2410DistanceSensorBase(LD2410BaseSensor):
    _attr_native_unit_of_measurement = "cm"
    _attr_device_class = SensorDeviceClass.DISTANCE

class LD2410EnergySensorBase(LD2410BaseSensor):
    _attr_native_unit_of_measurement = "%"

class LD2410MovingDistanceSensor(LD2410DistanceSensorBase):
    _attr_name = "Moving Distance"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_moving_distance"

    @property
    def native_value(self):
        return self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {}).get("moving_distance", 0)

class LD2410StaticDistanceSensor(LD2410DistanceSensorBase):
    _attr_name = "Static Distance"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_static_distance"

    @property
    def native_value(self):
        return self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {}).get("static_distance", 0)

class LD2410DetectionDistanceSensor(LD2410DistanceSensorBase):
    _attr_name = "Detection Distance"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_detection_distance"

    @property
    def native_value(self):
        return self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {}).get("detection_distance", 0)

class LD2410MovingEnergySensor(LD2410EnergySensorBase):
    _attr_name = "Moving Energy"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_moving_energy"

    @property
    def native_value(self):
        return self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {}).get("moving_energy", 0)

class LD2410StaticEnergySensor(LD2410EnergySensorBase):
    _attr_name = "Static Energy"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_static_energy"

    @property
    def native_value(self):
        return self.hass.data[DOMAIN].get(self.entry.entry_id, {}).get("latest_data", {}).get("static_energy", 0)
