# LD2410 Serial

Home Assistant custom component for integrating LD2410 mmWave presence sensors over a direct serial connection. It is based on the ESPHome LD2410 implementation: <https://github.com/esphome/esphome/tree/dev/esphome/components/ld2410>. This integration exposes similar entities and does not require an ESP32 board. It has been tested only with the HLK-LD2410B.

## Installation

### HACS

1. Open HACS in Home Assistant.
2. Search for "LD2410 Serial" and install.
3. Restart Home Assistant.

### Manual

1. Copy the `custom_components/ld2410_serial` directory to the `custom_components` directory of your Home Assistant installation.
2. Restart Home Assistant.

## Configuration

Go to **Settings** -> **Devices & Services** -> **Add Integration**, then search for "LD2410 Serial". You will be prompted to provide a serial port (for example, `/dev/ttyUSB0` or `/dev/ttyS1`).

The integration supports changing the detection gates, as well as the timeout.