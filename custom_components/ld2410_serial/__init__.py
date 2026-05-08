import asyncio
import logging
import serial
import struct
import threading
import time
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import dispatcher_send
import voluptuous as vol

from .const import (
    DOMAIN, 
    CONF_SERIAL_PORT, 
    CONF_BAUD_RATE, 
    DEFAULT_BAUD_RATE, 
    UPDATE_SIGNAL,
    CONF_MAX_MOVING,
    CONF_MAX_STATIC,
    CONF_TIMEOUT
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = ["sensor", "binary_sensor"]

HEADER = b'\xf4\xf3\xf2\xf1'
FOOTER = b'\xf8\xf7\xf6\xf5'

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the LD2410 Serial component from YAML (if present)."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LD2410 Serial from a config entry."""
    
    port = entry.data[CONF_SERIAL_PORT]
    baud = int(entry.data[CONF_BAUD_RATE])

    try:
        def open_serial():
            return serial.Serial(port, baud, timeout=1)
        ser = await hass.async_add_executor_job(open_serial)
    except serial.SerialException as err:
        _LOGGER.error("Error connecting to LD2410 on %s: %s", port, err)
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "serial": ser,
        "latest_data": {},
        "running": True
    }

    def read_loop():
        buffer = b''
        while hass.data[DOMAIN].get(entry.entry_id, {}).get("running", False):
            try:
                b1 = ser.read(1)
                if not b1:
                    continue
                buffer += b1
                if len(buffer) > 100:
                    buffer = buffer[-4:]
                if buffer.endswith(HEADER):
                    frame = HEADER
                    while hass.data[DOMAIN].get(entry.entry_id, {}).get("running", False):
                        b2 = ser.read(1)
                        if not b2:
                            break
                        frame += b2
                        if len(frame) > 100:
                            break
                        if frame.endswith(FOOTER):
                            parse_frame(frame)
                            time.sleep(0.5)
                            ser.reset_input_buffer()
                            break
            except Exception as e:
                if hass.data[DOMAIN].get(entry.entry_id, {}).get("running", False):
                    _LOGGER.error("Serial read error: %s", e)
                    time.sleep(1)

    def parse_frame(frame):
        try:
            target_state = frame[8]

            moving_distance = 0
            moving_energy = 0
            static_distance = 0
            static_energy = 0
            detection_distance = 0

            if target_state in (0x01, 0x03):
                moving_distance = frame[9] | (frame[10] << 8)
                moving_energy = frame[11]

            if target_state in (0x02, 0x03):
                static_distance = frame[12] | (frame[13] << 8)
                static_energy = frame[14]
            
            # byte 15 and 16 are combined detection distance
            detection_distance = frame[15] | (frame[16] << 8) if len(frame) > 16 else max(moving_distance, static_distance)

            hass.data[DOMAIN][entry.entry_id]["latest_data"] = {
                "target_state": target_state,
                "moving_distance": moving_distance,
                "static_distance": static_distance,
                "moving_energy": moving_energy,
                "static_energy": static_energy,
                "detection_distance": detection_distance,
            }
            
            hass.loop.call_soon_threadsafe(
                dispatcher_send, hass, f"{UPDATE_SIGNAL}_{entry.entry_id}"
            )

        except Exception as e:
            _LOGGER.error("Failed to parse LD2410 frame: %s", e)

    thread = threading.Thread(target=read_loop, daemon=True)
    hass.data[DOMAIN][entry.entry_id]["thread"] = thread
    thread.start()

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    max_moving = entry.options.get(CONF_MAX_MOVING, 4)
    max_static = entry.options.get(CONF_MAX_STATIC, 4)
    timeout = entry.options.get(CONF_TIMEOUT, 5)

    ser = hass.data[DOMAIN][entry.entry_id].get("serial")
    if not ser:
         return
    
    def apply_config():
        try:
            _LOGGER.info("Applying LD2410 config -> Moving: %s, Static: %s, Timeout: %ss", max_moving, max_static, timeout)
            # Enable Configuration Mode
            ser.write(b'\xfd\xfc\xfb\xfa\x04\x00\xff\x00\x01\x00\x04\x03\x02\x01')
            time.sleep(0.1)
            
            # Write max distance and timeout
            config_value = struct.pack("<H H H H H H H H H",
                0x0000, max_moving, 0x0000,
                0x0001, max_static, 0x0000,
                0x0002, timeout, 0x0000
            )
            length_bytes = struct.pack("<H", 2 + len(config_value))
            packet = b'\xfd\xfc\xfb\xfa' + length_bytes + b'\x60\x00' + config_value + b'\x04\x03\x02\x01'
            ser.write(packet)
            time.sleep(0.1)

            # Disable Configuration Mode
            ser.write(b'\xfd\xfc\xfb\xfa\x02\x00\xfe\x00\x04\x03\x02\x01')
            time.sleep(0.1)

            ser.reset_input_buffer()
        except Exception as e:
            _LOGGER.error("Failed to update LD2410 settings: %s", e)

    await hass.async_add_executor_job(apply_config)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        data["running"] = False
        data["serial"].close()

    return unload_ok