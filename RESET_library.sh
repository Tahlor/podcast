#!/bin/bash

sudo umount ~/Flash128
sudo fsck /dev/sda3 -y
sudo mount -all
cd /home/pi/Projects/podcast
python3 podcast_library.py
