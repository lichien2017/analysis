# coding=utf-8


import redisRW

import numpy as np
import os
import sys
import argparse
import glob
import time
import subprocess
import urllib2
import json
from time import sleep
from log import Logger

logger = None


#1. 检查拆分的文件路径是否存在,如果存在直接返回
#2. 检测视频文件是否存在,如果存在的话,拆分到文件路径上
#3. 都不存在,返回None
def checkvideo_data(videopath, splitpath):
    # 找到文件名和路径
    # 检查是否有目标目录，如果有则清空该目录
    # 调用ffmpeg解压
    try:
        # 1. 检查拆分的文件路径是否存在,如果存在直接返回
        if (os.path.exists(splitpath)):
            if(os.path.isdir("splitpath")):
                return splitpath
            #如果不是目录,那么删掉该文件,重新拆分
            else:
                cmdstr = "rm -rf %s" % splitpath
                # print('cmdstr is:', cmdstr)
                p = subprocess.Popen(cmdstr, shell=True)
                retcode = p.wait()

        #2. 检测视频文件是否存在,如果存在的话,拆分到文件路径上
        if (os.path.exists(videopath)):
            os.mkdir(splitpath)
            cmdstr = 'ffmpeg -i "%s" -r 0.5 -q:v 2 -f image2 "%s/%%d.jpg"' % (videopath, splitpath)
            print('cmdstr is:', cmdstr)
            p = subprocess.Popen(cmdstr, shell=True)
            retcode = p.wait()
            print('retcode =', retcode)
            return (splitpath)
        else:
            return None
    except:
        return None





def dosplit(config):
    print("config is:", config)

    queue = redisRW.MyQueue(db=config["dbnum"], host=config["host"])
    while (True):
        try:
            # print('step 0')
            datastr = queue.pop(config["queuename"])

            if (datastr == None):
                sleep(10)
                logger.info("Has no Data!")
                continue

            # datastr = unicode(datastr).encode("utf-8")

            data = json.loads(datastr)
            print("id is:", data["id"])

            print("data is:", data["data"])
            logger.info("get data; id is:%s;" % (data["id"]))

            if (len(data["data"]) < 3 or len(data["data"][0]) == 0):
                sleep(1)
                continue


            imgurl = data["data"][0]
            imgpath = data["data"][1]
            resppath = data["data"][2]

            flag = 0

            #print("imgurl:%s, imgpath:%s" % (imgurl, imgpath))

            try:
                videodata = checkvideo_data(imgpath, resppath)

                if videodata != None:
                    logger.info("get a videoData, ready to send queue: %s" %videodata)

                    #print("value is %f" % (value))
                    #logger.info("imgurl is %s; value is %f" % (imgurl, value))
                    resdata = data["resdata"]
                    ressplit = resdata.split(',')
                    if( len(ressplit)>=3):
                        flag = 1
                        queue.push(ressplit[2], datastr)

                else:
                    logger.info("get None videodata")
            except:
                sleep(1)
                None

            if(flag==0):
                setvalue = queue.set(data["id"], data["seq"], flag)
                #print("set queue id:%s, seq:%s, flag:%d, setval:%s" % (data["id"], data["seq"], flag, setvalue))

                # send a msg
                queue.push(data["resp"], data["resdata"])
                logger.info("queue resp:%s, resdata:%s" % (data["resp"], data["resdata"]))

        except:
            sleep(1)
            continue



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required arguments: input file.
    parser.add_argument(
        "configurepath",
        nargs='?',
        default="config.ini",
        help="Path to the configure file"
    )

    args = parser.parse_args()
    assert os.path.exists(args.configurepath), "The configure model file not exist."

    with open(args.configurepath, "r") as f:
        jsonconfig = json.load(f)

        logger = Logger(jsonconfig["logname"])
        dosplit(jsonconfig)
