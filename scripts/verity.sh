#!/bin/bash

# verify flashed firmware on esp8266
# usage:
#   ./flash path/to/firmware

sudo python esptool --port /dev/ttyUSB0 --baud 460800 verify_flash --flash_size=detect 0 ${1}
