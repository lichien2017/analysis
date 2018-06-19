import os
import sys
import argparse
import glob
import json
from time import sleep
from fuzzywuzzy import fuzz

import pytesseract
from PIL import Image
from PIL import ImageEnhance
import redisRW
from log import Logger
import traceback

reload(sys)
sys.setdefaultencoding('utf-8')

def getocrcode(imgpath, config,queue, logger):
    #check if already has
    if(queue.exists(config["ocrcache"], imgpath)):
        code = queue.get(config["ocrcache"], imgpath)
        print("code is:%s" % (code))
        logger.debug("cache code is:%s; imgpath is:%s" % (code, imgpath))
    else:
        #then ocr
        allpath = "%s/%s" %(config["filepath"],imgpath)
        print("allpath is:%s;" % (allpath))
        logger.debug("allpath is:%s;" % (allpath))

        img = Image.open(allpath)#.convert('P')

        enhancer = ImageEnhance.Color(img)
        enhancer = enhancer.enhance(0)
        enhancer = ImageEnhance.Contrast(enhancer)
        enhancer = enhancer.enhance(68.0)
        enhancer = ImageEnhance.Brightness(enhancer)
        enhancer = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(enhancer)
        img = enhancer.enhance(68.0)

        code = pytesseract.image_to_string(img, lang='chi_sim')
        img.close()
        #code = "1234556644324324324"
        code = code.replace(' ', '').replace('\n', '')
        print("allpath is:%s; code is:%s"%(allpath,code))
        logger.debug("allpath is:%s; code is:%s"%(allpath,code))
        queue.set(config["ocrcache"], imgpath,code)
        sleep(1)

    return code

def doocrcheck(config):
    queue = redisRW.MyQueue(db=config["dbnum"], host=config["host"])
    logger = Logger(config["logname"])
    while (True):
        try:
            print('ocr step 0, queuename is:', config["queuename"],config["host"],config["dbnum"])
            datastr = queue.pop(config["queuename"])

            if (datastr == None):
                sleep(10)
                continue

            # datastr = unicode(datastr).encode("utf-8")

            data = json.loads(datastr)
            print("resid is:%s, title is:%s" %(data["resid"], data["title"]))
            logger.info("resid is:%s"%(data["resid"]))

            flag = 0

            # print("imgurl:%s, imgpath:%s" % (imgurl, imgpath))

            try:
                imgs = data["imgs"]
                seqs = data["seqs"]
                imgslen = len(imgs)
                if(imgslen<=0 and imgslen!=len(seqs)):
                    print("img lens error")
                    logger.warning("img lens error")
                    sleep(1)
                    continue

                ratio = 0.0
                for i in range(0, imgslen):
                    ocrcode = getocrcode(imgs[i],config,queue, logger)
                    #ocrcode = "1234556644324324324"
                    #ratio = 10
                    ratio = fuzz.partial_ratio(ocrcode,data["title"])
                    print("ratio is:", ratio)
                    logger.info("ratio is: %f; code is:%s; title is:%s; img is:%s"
                                %(ratio, ocrcode, data["title"], imgs[i]))
                    if(ratio >=40.0):

                        #send a msg to queue

                        respdata = {"resid":data["resid"],"img":imgs[i],"seq":seqs[i]}
                        respjson = json.dumps(respdata)
                        print("respdata is:%s" %(respjson))
                        logger.debug("respdata is:%s" %(respjson))
                        queue.push(config["respqueuename"], respjson)
                        break
                if(ratio<50.0):
                    logger.debug("ratio is not match! data=%s"%(datastr))

            except:
                print("Exception is:%s", traceback.format_exc())
                logger.error("Exception is:%s", traceback.format_exc())
                sleep(1)
                None

            #setvalue = queue.set(data["id"], data["seq"], flag)
            # print("set queue id:%s, seq:%s, flag:%d, setval:%s" % (data["id"], data["seq"], flag, setvalue))

            # send a msg
            #queue.push(data["resp"], data["resdata"])
            #print("queue resp:%s, resdata:%s" % (data["resp"], data["resdata"]))
        except:
            sleep(1)
            logger.error("Exception is:%s", traceback.format_exc())
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
        doocrcheck(jsonconfig)