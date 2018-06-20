#!/bin/sh

cd /home/vista/Documents/train/auto_text_classification

flag=1

while [ "$flag" -eq 1 ]
do
    sleep 1

    #训练监听服务
    result=`ps -ef|grep "pythontrainserv trainservice.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythontrainserv trainservice.py trainconfig.ini 1>/dev/null 2>&1 &
    fi

done
