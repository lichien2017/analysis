# coding=utf-8

import os
import gzip
#import click
import argparse
import json
from time import sleep
import subprocess

import redisRW
import traceback
from log import Logger

import sys
reload(sys)
sys.setdefaultencoding('utf8')

logger = None
# args: 所有的参数,以便以后扩展
def watchtrain(args):


    queue = redisRW.MyQueue(db=args["dbnum"], host=args["host"])
    while (True):
        try:
            print('step 0')
            datastr = queue.pop(args["queuename"])

            if(datastr == None):
                sleep(10)
                continue

            print("datastr is:", datastr)

            datastr = unicode(datastr).encode("utf-8")

            data = json.loads(datastr)
            logger.info("get data; id is:%d"%(data["id"]))

            cmdstr = 'python traintext.py -i %d' % (data["id"])
            print('cmdstr is:', cmdstr)
            p = subprocess.Popen(cmdstr, shell=True)
            retcode = p.wait()
            print('retcode =', retcode)

            cmdstr2 = 'python traintext.py -i %d -s 1' % (data["id"])
            print('cmdstr2 is:', cmdstr2)
            p2 = subprocess.Popen(cmdstr2, shell=True)
            retcode2 = p2.wait()
            print('retcode2 =', retcode2)

        except KeyboardInterrupt:
            print('traceback.print_exc():%s' % traceback.print_exc())
            break
        except:
            print('traceback.print_exc():%s'%traceback.print_exc())
            sleep(1)
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required arguments: input file.
    parser.add_argument(
        "configurepath",
        nargs='?',
        default="trainconfig.ini",
        help="Path to the configure file"
    )

    args = parser.parse_args()
    assert os.path.exists(args.configurepath), "The configure model file not exist."

    with open(args.configurepath, "r") as f:
        jsonconfig = json.load(f)
        logger = Logger("watch_%s" % (jsonconfig["logname"]))

        watchtrain(jsonconfig)
