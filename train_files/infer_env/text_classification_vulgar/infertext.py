# coding=utf-8

import sys
import os
import gzip
#import click
import argparse
import json
from time import sleep
import random

import paddle.v2 as paddle
import traceback
import reader
from network_conf import nested_net
from utils import load_dict, load_reverse_dict
import redisRW
import filterflag

from log import Logger

logger = None

def get_model_path(modelpath, queue, key):
    try:
        #print("key is:%s"%key)
        #queue.sset(key=key, value='/mnt/train_files/autotrain/title/7/models/params_pass_00008.tar.gz')
        tmppath = queue.get(key=key)
        #print("tmppath is:%s"%tmppath)
        if(tmppath==None):
            return modelpath
        else:
            return tmppath
    except:
        logger.info('traceback.print_exc():%s' % traceback.print_exc())
        return modelpath


# args: 所有的参数,以便以后扩展
def infer( data_path, model_path, word_dict_path, batch_size, label_dict_path,args):

    def _infer_a_batch(inferer, test_batch, ids_2_word, ids_2_label):
        probs = inferer.infer(input=test_batch, field=["value"])
        print("label is:", ids_2_label )
        print("probs is:", probs)
        return (ids_2_label[probs.argmax()], probs[0][probs.argmax()])

    #设置队列,读取modelpath的配置也在这里
    queue = redisRW.MyQueue(db=args["dbnum"], host=args["host"])
    logger.info(" modelpath0 is: %s"%model_path)
    model_path = get_model_path(model_path, queue, args["model_key"])
    logger.info(" modelpath is: %s"%model_path)

    rootpath = os.path.dirname(os.path.dirname(model_path))
    word_dict_path = "%s/dict/word_dict" %rootpath
    label_dict_path = "%s/dict/label_dict" %rootpath

    assert os.path.exists(model_path), "The trained model does not exist."
    logger.info("Begin to predict...")
    use_default_data = (data_path is None)

    if use_default_data:
        word_dict = reader.imdb_word_dict()
        word_reverse_dict = dict((value, key)
                                 for key, value in word_dict.iteritems())

        # The reversed label dict of the imdb dataset 
        label_reverse_dict = {0: "positive", 1: "negative"}
        test_reader = reader.imdb_test(word_dict)
        class_num = 2
    else:
        assert os.path.exists(
            word_dict_path), "The word dictionary file does not exist"
        assert os.path.exists(
            label_dict_path), "The label dictionary file does not exist"

        word_dict = load_dict(word_dict_path)
        word_reverse_dict = dict((value, key)
                                 for key, value in word_dict.iteritems())
        label_reverse_dict = load_reverse_dict(label_dict_path)
        class_num = len(label_reverse_dict)

        #test_reader = reader.infer_reader(data_path, word_dict)()

    dict_dim = len(word_dict)

    # initialize PaddlePaddle.
    paddle.init(use_gpu=True, trainer_count=1)

    prob_layer = nested_net(dict_dim, class_num, is_infer=True)

    # load the trained models.
    parameters = paddle.parameters.Parameters.from_tar(
        gzip.open(model_path, "r"))
    inferer = paddle.inference.Inference(
        output_layer=prob_layer, parameters=parameters)

    #print("test_reader is:", test_reader)


    test_batch = []

    #print("args is:", args)
    #read infered data


    checkseq = "content"
    try:
        if(args["checktitle"] == 1):
            checkseq = "title"
    except:
        None

    docontinue = True
    refresh = args["refresh"]
    ntimes = refresh

    while (docontinue):
        try:
            ntimes = ntimes-1
            if(ntimes<0):
                ntimes = refresh
                tempmodelpath = get_model_path(model_path, queue, args["model_key"])
                if(tempmodelpath!=model_path):
                    docontinue = False
                    break

            # print('step 0')
            datastr = queue.pop(args["queuename"])

            if(datastr == None):
                sleep(10)
                continue

            #datastr = unicode(datastr).encode("utf-8")

            data = json.loads(datastr)
            print("id is:", data["id"])
            logger.info("get data; id is:%s"%(data["id"]))


            if(len(data["data"])==0):
                sleep(1)
                continue

            #print("Enter step 1")


            flag = 0
            if args['compute_flag'] == 1:
                if(len(data["data"][0])>0):
                    try:
                        #print("data.data[0] is:", data["data"][0])
                        datacontent = data["data"][0].encode("utf-8")
                        datacontent = filterflag.filter_tags(datacontent)

                        seq = data["seq"].encode("utf-8").lower()

                        print("datacontent is:", datacontent)
                        logger.info("datacontent:%s; seq is:%s" % (datacontent, seq))
                        if(seq==checkseq and len(datacontent)>=6):
                            #sleep(1)
                            #continue

                            item,doc = redisRW.infer_reader_content(datacontent, word_dict)
                            test_batch.append([item])
                            # if len(test_batch) == batch_size:
                            #     _infer_a_batch(inferer, test_batch, word_reverse_dict,
                            #                    label_reverse_dict)
                            #     test_batch = []

                            if len(test_batch):
                                label, value = _infer_a_batch(inferer, test_batch, word_reverse_dict,
                                               label_reverse_dict)
                                #label = 'normal'
                                #value = random.uniform(0.2,0.6)

                                print("%s is %f" %(label, value))
                                logger.info("%s is %f" %(label, value))

                                if (label == 'normal'):
                                    value = 1.0 - value
                                #update hashset
                                if(data["threshold"]<=value):
                                    flag = 1
                                else:
                                    flag = 0
                    except:
                        sleep(1)
                        None

            queue.set(data["id"], data["seq"], flag)
            #send a msg
            queue.push(data["resp"], data["resdata"])

            test_batch = []
            #sleep(10)
        except:
            sleep(1)
            test_batch = []
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

        infer(jsonconfig["data_path"],
              jsonconfig["model_path"],
              jsonconfig["word_dict_path"],
              jsonconfig["batch_size"],
              jsonconfig["label_dict_path"],
              jsonconfig)
