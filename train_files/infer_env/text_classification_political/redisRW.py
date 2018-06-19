# coding=utf-8

import redis
import json
from time import sleep
import jieba

import sys
reload(sys)
sys.setdefaultencoding('utf8')

#消息队列
class MyQueue(object):
    def __init__(self,db=7, host='localhost'):
        self.rcon = redis.Redis(host=host, port=6379, db=db)
        #print("db is:",db)
        # self.queue = queuename

    def pop(self, queuename):
        obj = self.rcon.rpop(queuename)
        return obj

    def push(self, queuename, obj):
        self.rcon.lpush(queuename, obj)

    def set(self, name, key, value):
        self.rcon.hset(name, key, value)

    def get(self, key):
        return(self.rcon.get(name=key))

    def sset(self, key, value):
        self.rcon.set(name=key, value=value )



def infer_reader_content(content, word_dict):
    """
    Reader interface for prediction

    :param data_dir: data directory
    :type data_dir: str
    :param word_dict: path of word dictionary,
        the dictionary must has a "UNK" in it.
    :type word_dict: Python dict
    """

    #with open(file_path, "r") as f:
    UNK_ID = word_dict['<unk>']
    seg_list = jieba.cut(content)
    #print("seg_list is :", seg_list)
    doc = ' '.join(seg_list).encode("utf-8")#.decode('unicode_escape')
    doc_ids = []

    for sent in doc.strip().split("。"):
        sent_ids = [word_dict.get(w, UNK_ID) for w in sent.split()]
        if sent_ids:
            doc_ids.append(sent_ids)
    return doc_ids, doc




