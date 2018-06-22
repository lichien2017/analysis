# coding=utf-8


import redisRW

import numpy as np
import os
import sys
import argparse
import glob
import time
from PIL import Image
from StringIO import StringIO
import traceback
import caffe
import urllib2
import json
from time import sleep
from log import Logger

logger = None

def resize_image(data, sz=(256, 256)):
    """
    Resize image. Please use this resize logic for best results instead of the
    caffe, since it was used to generate training dataset
    :param str data:
        The image data
    :param sz tuple:
        The resized image dimensions
    :returns bytearray:
        A byte array with the resized image
    """
    img_data = str(data)
    im = Image.open(StringIO(img_data))
    if im.mode != "RGB":
        im = im.convert('RGB')
    imr = im.resize(sz, resample=Image.BILINEAR)
    fh_im = StringIO()
    imr.save(fh_im, format='JPEG')
    fh_im.seek(0)
    return bytearray(fh_im.read())

def caffe_preprocess_and_compute(pimg, caffe_transformer=None, caffe_net=None,
    output_layers=None):
    """
    Run a Caffe network on an input image after preprocessing it to prepare
    it for Caffe.
    :param PIL.Image pimg:
        PIL image to be input into Caffe.
    :param caffe.Net caffe_net:
        A Caffe network with which to process pimg afrer preprocessing.
    :param list output_layers:
        A list of the names of the layers from caffe_net whose outputs are to
        to be returned.  If this is None, the default outputs for the network
        are returned.
    :return:
        Returns the requested outputs from the Caffe net.
    """
    if caffe_net is not None:

        # Grab the default output names if none were requested specifically.
        if output_layers is None:
            output_layers = caffe_net.outputs

        img_data_rs = resize_image(pimg, sz=(256, 256))
        image = caffe.io.load_image(StringIO(img_data_rs))

        H, W, _ = image.shape
        _, _, h, w = caffe_net.blobs['data'].data.shape
        h_off = max((H - h) / 2, 0)
        w_off = max((W - w) / 2, 0)
        crop = image[h_off:h_off + h, w_off:w_off + w, :]
        transformed_image = caffe_transformer.preprocess('data', crop)
        transformed_image.shape = (1,) + transformed_image.shape

        input_name = caffe_net.inputs[0]
        all_outputs = caffe_net.forward_all(blobs=output_layers,
                    **{input_name: transformed_image})

        outputs = all_outputs[output_layers[0]][0].astype(float)
        return outputs[1]
    else:
        return 0.1

def getimg_data(imgpath, imgurl):
    try:
        if(os.path.exists(imgpath)):
            #print("using file")
            logger.info("using file path is:%s;" % (imgpath))
            image_data = open(imgpath).read()
            return image_data
        else:
            #print("using net")
            logger.info("using net imgurl is:%s;" % (imgurl))

            dirname = os.path.dirname(imgpath)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            req = urllib2.Request(imgurl)
            res_data = urllib2.urlopen(req,timeout=15)
            res = res_data.read()
            open(imgpath, "wb").write(res)
            return res
    except:
        return None

def saveimg(srcpath, targetpath, imgdata):
    print('srcpath is %s, targetpath is %s'%(srcpath, targetpath))

    dirname = os.path.dirname(targetpath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if (os.path.exists(srcpath)):
        open(targetpath, "wb").write(open(srcpath, "rb").read())
    else:
        open(targetpath, "wb").write(imgdata)


def inferimg(config):
    pycaffe_dir = os.path.dirname(__file__)

    print("config is:", config)
    model_def = config["model_def"].encode("ascii")
    pretrained_model = config["pretrained_model"].encode("ascii")
    # Pre-load caffe model.
    nsfw_net = caffe.Net(model_def,  # pylint: disable=invalid-name
                         pretrained_model,
                         caffe.TEST)

    # Load transformer
    # Note that the parameters are hard-coded for best results
    caffe_transformer = caffe.io.Transformer({'data': nsfw_net.blobs['data'].data.shape})
    caffe_transformer.set_transpose('data', (2, 0, 1))  # move image channels to outermost
    caffe_transformer.set_mean('data', np.array([104, 117, 123]))  # subtract the dataset-mean value in each channel
    caffe_transformer.set_raw_scale('data', 255)  # rescale from [0, 1] to [0, 255]
    caffe_transformer.set_channel_swap('data', (2, 1, 0))  # swap channels from RGB to BGR

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

            if config['compute_flag'] == 1:
                #print("imgurl:%s, imgpath:%s" % (imgurl, imgpath))

                try:
                    imgdata = getimg_data(imgpath, imgurl)

                    if imgdata != None:
                        logger.info("get a imgData, ready to compute")
                        value = caffe_preprocess_and_compute(imgdata,
                                                             caffe_transformer=caffe_transformer,
                                                             caffe_net=nsfw_net,
                                                             output_layers=['prob'])


                        #print("value is %f" % (value))
                        logger.info("imgurl is %s; value is %f" % (imgurl, value))
                        # update hashset
                        if (data["threshold"] <= value):
                            flag = 1
                            saveimg(imgpath, resppath, imgdata)

                        else:
                            flag = 0
                    else:
                        logger.info("get None imgData")
                except:
                    logger.info('traceback.print_exc():%s' % traceback.print_exc())
                    sleep(1)
                    None


            setvalue = queue.set(data["id"], data["seq"], flag)
            #print("set queue id:%s, seq:%s, flag:%d, setval:%s" % (data["id"], data["seq"], flag, setvalue))

            # send a msg
            queue.push(data["resp"], data["resdata"])
            logger.info("queue resp:%s, resdata:%s" % (data["resp"], data["resdata"]))
            sleep(0.3)

        except:
            logger.info('traceback.print_exc():%s' % traceback.print_exc())
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
        inferimg(jsonconfig)
