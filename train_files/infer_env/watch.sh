#!/bin/sh

cd /home/vista/Documents/baseservice

flag=1

while [ "$flag" -eq 1 ]
do
    sleep 1

    #图片解析政治有害
    result=`ps -ef|grep "pythonservice img_classification_political/inferimg.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice img_classification_political/inferimg.py img_classification_political/config.ini 1>/dev/null 2>&1 &
    fi

    #图片解析色情
    result=`ps -ef|grep "pythonservice img_classification_vulgar/inferimg.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice img_classification_vulgar/inferimg.py img_classification_vulgar/config.ini 1>/dev/null 2>&1 &
    fi

    #图片解析标题党
    result=`ps -ef|grep "pythonservice img_classification_title/inferimg.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice img_classification_title/inferimg.py img_classification_title/config.ini 1>/dev/null 2>&1 &
    fi

    #文本解析政治有害
    result=`ps -ef|grep "pythonservice text_classification_political/infertext.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice text_classification_political/infertext.py text_classification_political/config.ini 1>/dev/null 2>&1 &
    fi

    #文本解析色情
    result=`ps -ef|grep "pythonservice text_classification_vulgar/infertext.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice text_classification_vulgar/infertext.py text_classification_vulgar/config.ini 1>/dev/null 2>&1 &
    fi

    #文本解析标题党
    result=`ps -ef|grep "pythonservice text_classification_title/infertext.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice text_classification_title/infertext.py text_classification_title/config.ini 1>/dev/null 2>&1 &
    fi

    #视频分解
    result=`ps -ef|grep "pythonservice videosplit/video_split.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice videosplit/video_split.py videosplit/config.ini 1>/dev/null 2>&1 &
    fi

    #视频解析色情
    result=`ps -ef|grep "pythonservice video_class_vulgar/infervideo.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice video_class_vulgar/infervideo.py video_class_vulgar/config.ini 1>/dev/null 2>&1 &
    fi

    #视频解析标题党
    result=`ps -ef|grep "pythonservice video_class_title/infervideo.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice video_class_title/infervideo.py video_class_title/config.ini 1>/dev/null 2>&1 &
    fi

    #视频解析政治有害
    result=`ps -ef|grep "pythonservice video_class_political/infervideo.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice video_class_political/infervideo.py video_class_political/config.ini 1>/dev/null 2>&1 &
    fi
    
    #OCR处理图片
    result=`ps -ef|grep "pythonservice ocrmatch/ocrcheck.py" | grep -v "grep"`

    if [ -z "$result" ]; then
        nohup pythonservice ocrmatch/ocrcheck.py ocrmatch/config.ini 1>/dev/null 2>&1 &
    fi

done
