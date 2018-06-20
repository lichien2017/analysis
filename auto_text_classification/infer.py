# coding=utf-8

import sys
import os
import gzip
import click
import argparse
import json
import paddle.v2 as paddle

import reader
from network_conf import nested_net
from utils import load_dict, load_reverse_dict

from log import Logger
logger = None
@click.command('infer')
@click.option(
    "--data_path",
    default=None,
    help=("The path of data for inference (default: None). "
          "If this parameter is not set, "
          "imdb test dataset will be used."))
@click.option(
    "--model_path", type=str, required=True, help="The path of saved model.")
@click.option(
    "--word_dict_path",
    type=str,
    default=None,
    help=("The path of word dictionary (default: None). "
          "If this parameter is not set, imdb dataset will be used."))
@click.option(
    "--label_dict_path",
    type=str,
    default=None,
    help=("The path of label dictionary (default: None)."
          "If this parameter is not set, imdb dataset will be used. "))
@click.option(
    "--batch_size",
    type=int,
    default=32,
    help="The number of examples in one batch (default: 32).")
def infer(data_path, model_path, word_dict_path, batch_size, label_dict_path):
    # data_path = config["data_path"]
    # model_path = config["model_path"]
    # word_dict_path = config["word_dict_path"]
    # batch_size = config["batch_size"]
    # label_dict_path = config["label_dict_path"]

    def _infer_a_batch(inferer, test_batch, ids_2_word, ids_2_label):
        print("test_batch format is:%s" % (json.dumps(test_batch)))
        probs = inferer.infer(input=test_batch, field=["value"])
        print("label is:", ids_2_label)
        print("probs is:", probs)
        assert len(probs) == len(test_batch)
        for word_ids, prob in zip(test_batch, probs):
            sent_ids = []
            for sent in word_ids[0]:
                sent_ids.extend(sent)
            word_text = " ".join([ids_2_word[id] for id in sent_ids])
            print("%s\t%s\t%s" % (ids_2_label[prob.argmax()],
                                  " ".join(["{:0.4f}".format(p)
                                            for p in prob]), word_text))
        return (ids_2_label[1], probs[0][1])

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
        test_reader = reader.infer_reader(data_path, word_dict)()

    dict_dim = len(word_dict)

    # initialize PaddlePaddle.
    paddle.init(use_gpu=True, trainer_count=1)

    prob_layer = nested_net(dict_dim, class_num, is_infer=True)

    # load the trained models.
    parameters = paddle.parameters.Parameters.from_tar(
        gzip.open(model_path, "r"))
    inferer = paddle.inference.Inference(
        output_layer=prob_layer, parameters=parameters)

    test_batch = []
    for idx, item in enumerate(test_reader):
        print("item[0] is:", item[0])
        print("idx is:",idx)
        test_batch.append([item[0]])
        if len(test_batch) == batch_size:
            flabel, fvalue = _infer_a_batch(inferer, test_batch, word_reverse_dict, label_reverse_dict)
            print("%s is %f" % (flabel, fvalue))
            test_batch = []

    if len(test_batch):
        flabel, fvalue = _infer_a_batch(inferer, test_batch, word_reverse_dict, label_reverse_dict)
        print("%s is %f" % (flabel, fvalue))
        test_batch = []


if __name__ == "__main__":
    logger = Logger('test.log')
    infer()
