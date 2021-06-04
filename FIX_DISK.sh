#!/bin/bash

mountpoint ~/Flash128/
# sudo umount ~/Flash128 -l
sudo umount ~/Flash128
sudo fsck /dev/sda3 -y
sudo mount -all
#  chgrp -R pi ~/Flash128/* && chown -R pi ~/Flash128/* && chmod -R 777 ~/Flash128/*
