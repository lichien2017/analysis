#!/bin/sh

cd /work/auto_text_classification

flag=1

while [ "$flag" -eq 1 ]
do
    sleep 1

    #训练监听服务
    result=`ps -ef|grep "python trainservice.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup python trainservice.py trainconfig.ini 1>/dev/null 2>&1 &
    fi

done
