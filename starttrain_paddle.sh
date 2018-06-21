#!/bin/sh

cd /work/auto_text_classification
nohup /bin/sh ./watchtrain_paddle.sh 1>/dev/null 2>&1 &
#防止docker容器退出
/bin/bash
