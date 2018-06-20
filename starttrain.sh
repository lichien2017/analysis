#!/bin/sh

cd /home/vista/Documents/train/auto_text_classification
nohup ./watchtrain.sh 1>/dev/null 2>&1 &
