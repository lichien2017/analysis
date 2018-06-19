# coding=utf-8


import redisRW

import numpy as np
import os
import sys
import argparse
import glob
import time
import urllib2
import json
from time import sleep
from log import Logger
import traceback
import nsfw_batch

logger = None


#1. 检查拆分的文件路径是否存在,如果存在直接返回
#2. 检测视频文件是否存在,如果存在的话,拆分到文件路径上
#3. 都不存在,返回None
def checkvideo_data(videopath, splitpath):
    # 找到文件名和路径
    # 检查是否有目标目录，如果有则清空该目录
    # 调用ffmpeg解压
    try:
        logger.info("splitpath is: %s"%splitpath)
        # 1. 检查拆分的文件路径是否存在,如果存在直接返回
        if (os.path.exists(splitpath) and os.path.isdir(splitpath)):
                return splitpath
        return None
    except:
        return None





def infervideo(config):
    print("config is:", config)

    queue = redisRW.MyQueue(db=config["dbnum"], host=config["host"])
    nsfw_net,caffe_transformer = nsfw_batch.initnet(config["model_def"].encode("ascii"),
                                                      config["pretrained_model"].encode("ascii") )
    while (True):
        try:
            # 获取数据
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

            #if (len(data["data"]) < 3 or len(data["data"][0]) == 0):
            #    sleep(1)
            #    continue

            # 拆分后的目录路径保存在resppath中
            imgurl = data["data"][0]
            imgpath = data["data"][1]
            resppath = data["data"][2]


            #print("imgurl:%s, resppath:%s" % (imgurl, resppath))

            #无论结果,都需要返回
            flag = 0
            res_senses = ""
            res_data = {"save_path": resppath, "images":[] }
            #res_data["save_path"] = resppath
            #res_data["images"] = []


            try:
                videodata = checkvideo_data(imgpath, resppath)

                if videodata != None:
                    logger.info("get a imgs path, ready to process: %s, %f, %s, %s"
                                %(videodata,data["threshold"], config["model_def"], config["pretrained_model"]))

                    scores, senses = nsfw_batch.checkpath(imgspath=videodata, threshold=data["threshold"],
                                                          nsfw_net=nsfw_net, caffe_transformer=caffe_transformer)

                    logger.info("scores is:%s;  senses is:%s" % (scores, senses))
                    if(len(senses)>0):
                        flag = 1
                        res_data["images"] = senses
                        res_senses = json.dumps(res_data)
                        #data["resdata"] = "%s,%s" %(data["resdata"], res_senses)
                        #logger.info("scores is:%s;  senses is:%s" %(scores, res_senses))

                else:
                    logger.info("get None imgs")
            except:
                print('traceback.print_exc():%s' % traceback.print_exc())
                sleep(1)
                None

            if(flag==0):
                setvalue = queue.set(data["id"], data["seq"], flag)
            else:
                setvalue = queue.set(data["id"], data["seq"], res_senses)
                #print("set queue id:%s, seq:%s, flag:%d, setval:%s" % (data["id"], data["seq"], flag, setvalue))

            # send a msg
            queue.push(data["resp"], data["resdata"])
            logger.info("queue resp:%s, resdata:%s" % (data["resp"], data["resdata"]))
            sleep(0.2)

        except:
            print('traceback.print_exc():%s' % traceback.print_exc())
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
        infervideo(jsonconfig)
