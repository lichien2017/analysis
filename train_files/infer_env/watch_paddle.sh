#!/bin/sh



flag=1

while [ "$flag" -eq 1 ]
do
    sleep 1

    #文本解析政治有害
    result=`ps -ef|grep "python text_classification_political/infertext.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup python text_classification_political/infertext.py text_classification_political/config.ini 1>/dev/null 2>&1 &
    fi

    #文本解析色情
    result=`ps -ef|grep "python text_classification_vulgar/infertext.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup python text_classification_vulgar/infertext.py text_classification_vulgar/config.ini 1>/dev/null 2>&1 &
    fi

    #文本解析标题党
    result=`ps -ef|grep "python text_classification_title/infertext.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup python text_classification_title/infertext.py text_classification_title/config.ini 1>/dev/null 2>&1 &
    fi


done
