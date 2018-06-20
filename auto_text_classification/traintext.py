# coding=utf-8
import os
import sys
import gzip
#import click
import argparse
import json
from decimal import *

import paddle.v2 as paddle

import reader
from network_conf import nested_net
from utils import build_word_dict, build_label_dict, load_dict, copyFiles, copyFile, load_reverse_dict
from config import TrainerConfig as conf
import redisRW
from DBUtils import DBUtils

from log import Logger
import sys
reload(sys)
sys.setdefaultencoding('utf8')

logger = None
# @click.command('train')
# @click.option(
#     "--train_data_dir",
#     default=None,
#     help=("The path of training dataset (default: None). "
#           "If this parameter is not set, "
#           "imdb dataset will be used."))
# @click.option(
#     "--test_data_dir",
#     default=None,
#     help=("The path of testing dataset (default: None). "
#           "If this parameter is not set, "
#           "imdb dataset will be used."))
# @click.option(
#     "--word_dict_path",
#     type=str,
#     default=None,
#     help=("The path of word dictionary (default: None). "
#           "If this parameter is not set, imdb dataset will be used. "
#           "If this parameter is set, but the file does not exist, "
#           "word dictionay will be built from "
#           "the training data automatically."))
# @click.option(
#     "--label_dict_path",
#     type=str,
#     default=None,
#     help=("The path of label dictionary (default: None). "
#           "If this parameter is not set, imdb dataset will be used. "
#           "If this parameter is set, but the file does not exist, "
#           "label dictionay will be built from "
#           "the training data automatically."))
# @click.option(
#     "--model_save_dir",
#     type=str,
#     default="models",
#     help="The path to save the trained models (default: 'models').")
#训练模型
def train(database, config, taskdata):
    #train_data_dir, test_data_dir, word_dict_path, label_dict_path,model_save_dir):
    """
    :params train_data_path: The path of training data, if this parameter
        is not specified, imdb dataset will be used to run this example
    :type train_data_path: str
    :params test_data_path: The path of testing data, if this parameter
        is not specified, imdb dataset will be used to run this example
    :type test_data_path: str
    :params word_dict_path: The path of word dictionary, if this parameter
        is not specified, imdb dataset will be used to run this example
    :type word_dict_path: str
    :params label_dict_path: The path of label dictionary, if this parameter
        is not specified, imdb dataset will be used to run this example
    :type label_dict_path: str
    :params model_save_dir: dir where models saved
    :type model_save_dir: str
    """

    root_path = config["root_path"]
    train_data_dir = None
    test_data_dir = None
    word_dict_path = "%s/%d/%s" %(root_path, taskdata["id"], config["word_dict_path"])
    label_dict_path = "%s/%d/%s" %(root_path, taskdata["id"], config["label_dict_path"])
    template_label_path = "%s/template/%s" % (root_path, config["label_dict_path"])
    model_save_dir = "%s/%d/%s" %(root_path, taskdata["id"], config["model_save_dir"])

    print("model_save_dir is:%s"%model_save_dir )

    if train_data_dir is not None:
        assert word_dict_path and label_dict_path, (
            "The parameter train_data_dir, word_dict_path, label_dict_path "
            "should be set at the same time.")

    dict_dirname = os.path.dirname(word_dict_path)
    if not os.path.exists(dict_dirname):
        os.makedirs(dict_dirname)

    if not os.path.exists(model_save_dir):
        os.makedirs(model_save_dir)

    use_default_data = False

    if use_default_data:
        None
    else:
        if word_dict_path is None or not os.path.exists(word_dict_path):
            logger.info(("Word dictionary is not given, the dictionary "
                         "is automatically built from the training data."))

        # build the word dictionary to map the original string-typed
        # words into integer-typed index
        reader.build_word_dict_db(
            db=database,
            taskdata = taskdata,
            splitwordpath = config["splitwordpath"],
            save_path=word_dict_path,
            use_col=1,
            cutoff_fre=0)

        if not os.path.exists(label_dict_path):
            logger.info(("Label dictionary is not given, the dictionary "
                         "is automatically built from the training data."))
            copyFile(template_label_path, label_dict_path)
            # build the label dictionary to map the original string-typed
            # label into integer-typed index
            # build_label_dict(
            #     data_dir=train_data_dir, save_path=label_dict_path, use_col=0)

        word_dict = load_dict(word_dict_path)
        label_dict = load_dict(label_dict_path)

        print("label_dict is:", label_dict)

        class_num = len(label_dict)
        logger.info("Class number is : %d." % class_num)

        train_reader = paddle.batch(
            paddle.reader.shuffle(
                reader.train_reader(database,taskdata, config["splitwordpath"],word_dict, label_dict),
                buf_size=conf.buf_size),
            batch_size=conf.batch_size)

        if test_data_dir is not None:
            # here, because training and testing data share a same format,
            # we still use the reader.train_reader to read the testing data.
            test_reader = paddle.batch(
                paddle.reader.shuffle(
                    reader.train_reader(database,taskdata, config["splitwordpath"], word_dict, label_dict),
                    buf_size=conf.buf_size),
                batch_size=conf.batch_size)
        else:
            test_reader = None

    dict_dim = len(word_dict)

    logger.info("Length of word dictionary is : %d." % (dict_dim))

    paddle.init(use_gpu=conf.use_gpu, trainer_count=conf.trainer_count)

    logger.info("paddle.init is over")
    # create optimizer
    adam_optimizer = paddle.optimizer.Adam(
        learning_rate=conf.learning_rate,
        regularization=paddle.optimizer.L2Regularization(
            rate=conf.l2_learning_rate),
        model_average=paddle.optimizer.ModelAverage(
            average_window=conf.average_window))

    logger.info("adam_optimizer is over")
    # define network topology.
    cost, prob, label = nested_net(dict_dim, class_num, is_infer=False)

    logger.info("nested_net is over")

    # create all the trainable parameters.
    parameters = paddle.parameters.create(cost)

    logger.info("paddle.parameters is over")

    # create the trainer instance.
    trainer = paddle.trainer.SGD(
        cost=cost,
        extra_layers=paddle.evaluator.auc(input=prob, label=label),
        parameters=parameters,
        update_equation=adam_optimizer)

    logger.info("paddle.trainer.SG is over")
    # feeding dictionary
    feeding = {"word": 0, "label": 1}

    def _event_handler(event):
        """
        Define the end batch and the end pass event handler.
        """
        if isinstance(event, paddle.event.EndIteration):
            if event.batch_id % conf.log_period == 0:
                logger.info("Pass %d, Batch %d, Cost %f, %s\n" % (
                    event.pass_id, event.batch_id, event.cost, event.metrics))

        if isinstance(event, paddle.event.EndPass):
            if test_reader is not None:
                result = trainer.test(reader=test_reader, feeding=feeding)
                logger.info("Test at Pass %d, %s \n" % (event.pass_id,
                                                        result.metrics))
            with gzip.open(
                    os.path.join(model_save_dir, "params_pass_%05d.tar.gz" %
                                 event.pass_id), "w") as f:
                trainer.save_parameter_to_tar(f)

    # begin training network
    trainer.train(
        reader=train_reader,
        event_handler=_event_handler,
        feeding=feeding,
        num_passes=conf.num_passes)

    logger.info("Training has finished.")

    model_path = "%s/params_pass_00008.tar.gz"%(model_save_dir)
    if(os.path.exists(model_path)):
        database.update_train_job(taskdata, model_path, 0, 2)

    #copyFiles(config["dict_path"], config["target_dict_path"])
    #copyFiles(config["model_save_dir"],config["target_model_path"])

#测试模型
def test(database, config, taskdata):
    def _infer_a_batch(inferer, test_batch, ids_2_word, ids_2_label):
        probs = inferer.infer(input=test_batch, field=["value"])
        print("label is:", ids_2_label )
        print("probs is:", probs)
        return (ids_2_label[probs.argmax()], probs[0][probs.argmax()])

    root_path = config["root_path"]
    train_data_dir = None
    test_data_dir = None
    word_dict_path = "%s/%d/%s" % (root_path, taskdata["id"], config["word_dict_path"])
    label_dict_path = "%s/%d/%s" % (root_path, taskdata["id"], config["label_dict_path"])
    template_label_path = "%s/template/%s" % (root_path, config["label_dict_path"])
    model_path = taskdata["output_model_path"]

    assert os.path.exists(model_path), "The trained model does not exist."
    logger.info("Begin to predict...")
    use_default_data = False

    if use_default_data:
        None
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
        #test_reader = database.tests_data_reader(taskdata)
        test_reader = reader.test_reader(database,taskdata,config["splitwordpath"], word_dict,label_reverse_dict)()

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
    allcount=0
    matchcount=0
    for idx, (sampleid, res_content,standard) in enumerate(test_reader):
        print("sampleid is:%d; content is:%s; standard is:%d" %(sampleid, res_content, standard))
        print("idx is:",idx)
        allcount = allcount+1
        test_batch.append([res_content])

        label, value = _infer_a_batch(inferer, test_batch, word_reverse_dict,
                       label_reverse_dict)
        if (label == 'normal'):
            value = 1.0 - value

        if(value>=taskdata["limit_ratio"]):
            result = 1
        else:
            result = 0

        matchcount = matchcount+(1 if (result==standard) else 0)

        test_batch = []

        database.update_test_result(sampleid=sampleid, result=result, matchratio=value)


    if(allcount>0):
        matchratio = Decimal(matchcount)/Decimal(allcount)
    else:
        matchratio = 0.0

    print("matchratio is:%f" %(matchratio))
    database.update_train_job(taskdata, model_path, matchratio, 3)
    database.insert_train_model(taskdata)


#开始训练,传入taskid和配置路径
def starttrain(jsonconfig, taskid):
    db = DBUtils(jsonconfig["mysql"])

    job = db.get_train_job(taskid=taskid)
    if(job !=None):
        print("job is:", job)
        if(job["res_type"]==0):
            tag = "text_"+job["rule_tag"]
            train(db, jsonconfig[tag], job)

def starttest(jsonconfig, taskid):
    db = DBUtils(jsonconfig["mysql"])

    job = db.get_train_job(taskid=taskid)
    if(job !=None):
        print("job is:", job)
        if(job["res_type"]==0):
            tag = "text_"+job["rule_tag"]
            test(db, jsonconfig[tag], job)


#传入训练任务的数据
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required arguments: input file.
    parser.add_argument(
        "configurepath",
        nargs='?',
        default="trainconfig.ini",
        help="Path to the configure file"
    )

    # Required arguments: input taskid, type=int.
    parser.add_argument(
        "-i", "--taskid",
        help="taskid in DB",
        type=int,
        required=True

    )

    # Required arguments: switch, type=int. -s 0:train  1:test
    parser.add_argument(
        "-s", "--switch",
        help="switch flag; 0:train  1:test",
        type=int,
        default=0
    )

    args = parser.parse_args()
    assert os.path.exists(args.configurepath), "The configure model file not exist."


    with open(args.configurepath, "r") as f:
        jsonconfig = json.load(f)


        if(args.switch==0):
            logger = Logger("train_%s" % (jsonconfig["logname"]))
            starttrain(jsonconfig, args.taskid)
        else:
            logger = Logger("test_%s" % (jsonconfig["logname"]))
            starttest(jsonconfig, args.taskid)



