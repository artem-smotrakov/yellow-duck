#!/bin/bash

# erase flash

sudo esptool --port /dev/ttyUSB0 erase_flash
