# coding=utf-8

import os
from mysqldb.mysql_helper import MySQLHelper
from DataCollection.data_collection import Collector


def getsrc():
    collect = Collector()
    news = collect.news_reader()
    #逐条枚举数据,生成文件
    for idx, item,content in enumerate(news):
        print("idx is:", idx)
        print("item is:", item)
        print("content is:", item)





if __name__ == "__main__":
    getsrc()
