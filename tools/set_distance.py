import serial
import time
import struct
import argparse

BAUD = 256000

CMD_HEADER = b'\xfd\xfc\xfb\xfa'
CMD_FOOTER = b'\x04\x03\x02\x01'

def send_command(ser, cmd_word, value_bytes=b''):
    length = len(cmd_word) + len(value_bytes)
    length_bytes = struct.pack("<H", length)
    
    packet = CMD_HEADER + length_bytes + cmd_word + value_bytes + CMD_FOOTER
    print(f"Sending: {packet.hex(' ')}")
    ser.write(packet)
    time.sleep(0.1)
    
    # Read response
    resp = ser.read(ser.in_waiting)
    if resp:
        print(f"Received: {resp.hex(' ')}\n")
    else:
        print("No response received.\n")

def main():
    parser = argparse.ArgumentParser(description="Set LD2410 max distances and timeout.")
    parser.add_argument("port", type=str, help="Serial port to use (e.g. /dev/ttyS2)")
    parser.add_argument("--moving", type=int, default=4, help="Max moving gate (default: 4)")
    parser.add_argument("--static", type=int, default=4, help="Max static gate (default: 4)")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds (default: 5)")
    args = parser.parse_args()

    print(f"Opening serial port {args.port}...")
    try:
        ser = serial.Serial(args.port, BAUD, timeout=1)
    except Exception as e:
        print(f"Failed to open port: {e}")
        return

    # Enable Configuration Mode
    print("Enabling Configuration Mode...")
    send_command(ser, b'\xff\x00', b'\x01\x00')

    # Setting Max Distance and Timeout
    max_moving = args.moving
    max_static = args.static
    timeout = args.timeout
    
    print(f"Applying Distance Gates -> Moving: {max_moving}, Static: {max_static}, Timeout: {timeout}s")
    
    # The struct is 18 bytes:
    # 0x0000 (2b) | max_moving (2b) | 0x0000 (2b) -> 6 bytes
    # 0x0001 (2b) | max_static (2b) | 0x0000 (2b) -> 6 bytes
    # 0x0002 (2b) | timeout (2b)    | 0x0000 (2b) -> 6 bytes
    
    config_value = struct.pack("<H H H H H H H H H",
        0x0000, max_moving, 0x0000,
        0x0001, max_static, 0x0000,
        0x0002, timeout, 0x0000
    )
    
    send_command(ser, b'\x60\x00', config_value)

    # Disable Configuration Mode
    print("Disabling Configuration Mode...")
    send_command(ser, b'\xfe\x00')

    max_dist = max(max_moving, max_static) * 0.75
    print(f"Success! Your LD2410 sensor settings (Moving: {max_moving}, Static: {max_static}, Timeout: {timeout}s) have been configured. (Max Distance: {max_dist:.2f} m)")
    ser.close()

if __name__ == "__main__":
    main()
