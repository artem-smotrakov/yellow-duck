#!/bin/bash

# flash esp8266 with specified firmware
# usage:
#   ./flash path/to/firmware

sudo python esptool --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 ${1}
