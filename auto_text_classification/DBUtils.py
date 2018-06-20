# coding=utf-8
import MySQLdb
from hashlib import md5
from datetime import datetime
from multiprocessing import Process
from time import sleep


class DBUtils:
    #db_user = 'root'
    #db_host = '192.168.10.176'
    #db_passwd = '123456'
    #db_charset = 'utf8'
    #dbname = 'dbname'

    def __init__(self, config):
        self.db_user = config["db_user"]
        self.db_host = config["db_host"]
        self.db_passwd = config["db_passwd"]
        self.db_charset = config["db_charset"]
        self.db_name = config["db_name"]
        
        self.db_session = MySQLdb.connect(user=self.db_user, host=self.db_host, db=self.db_name,
                                               passwd=self.db_passwd, charset=self.db_charset)


    #读取需要训练的任务数据
    #传入training_jobs表的数据
    def trains_data_reader(self, taskdata):
        db_cursor = self.db_session.cursor(MySQLdb.cursors.DictCursor)

        sql = """select * from training_traininglibrary
                where tag in (%s)
               """ % (taskdata["training_library_tags"])

        print("sql is:", sql)
        # 根据jobid查找所有的训练样本数据
        row_count = db_cursor.execute(sql)
        # 获取所有数据
        result = db_cursor.fetchone()

        while result != None:
            yield(result["res_content"],result["isbad"])

            result = db_cursor.fetchone()
        db_cursor.close()

    # 读取需要测试的任务数据
    # 传入training_jobs表的数据
    def tests_data_reader(self, taskdata):
        db_cursor = self.db_session.cursor(MySQLdb.cursors.DictCursor)

        # 根据jobid查找所有的测试样本数据
        row_count = db_cursor.execute("""
                            select * from training_sample
                            where jobid = %d
                            """ % (taskdata["id"]))
        # 获取所有数据
        result = db_cursor.fetchone()

        while result != None:
            yield (result["id"], result["res_content"], result["standard"])

            result = db_cursor.fetchone()
        db_cursor.close()


    #更新训练job表：
    #包括模型文件路径、匹配度等
    def update_train_job(self, taskdata, modelpath,matchratio, status, auto_commit=True):
        db_cursor = self.db_session.cursor()
        row_count = db_cursor.execute("""
                            update training_jobs set 
                            output_model_path='%s', status=2, match_ratio = %f, status = %d                             
                            where id = %d
                            """ % (modelpath, matchratio,status, taskdata["id"]))

        if auto_commit:
            self.db_session.commit()

        db_cursor.close()

    #插入模型表
    def insert_train_model(self, taskdata, auto_commit=True):
        db_cursor = self.db_session.cursor()
        row_count = db_cursor.execute("""
                                    insert into training_models(model_name,model_path,rule_tag,isdefault,
                                    res_type,jobid,match_ratio,createtime)
                                    select title,output_model_path,rule_tag,0,res_type,id,match_ratio,'%s' 
                                    from training_jobs                                                      
                                    where id = %d
                                    """ % (datetime.now().strftime('%Y-%m-%d %H:%M:%S' ),taskdata["id"]))

        if auto_commit:
            self.db_session.commit()

        db_cursor.close()

    #更新测试结果
    def update_test_result(self, sampleid, result,matchratio, auto_commit=True):
        db_cursor = self.db_session.cursor()
        row_count = db_cursor.execute("""
                            update training_sample set 
                            result=%d, match_ratio = %f                             
                            where id = %d
                            """ % (result, matchratio,sampleid))

        if auto_commit:
            self.db_session.commit()

        db_cursor.close()


    def get_train_job(self,taskid):
        db_cursor = self.db_session.cursor(MySQLdb.cursors.DictCursor)
        row_count = db_cursor.execute("""
                                    select * from training_jobs                            
                                    where id = %d
                                    """ % (taskid))
        result = db_cursor.fetchone()
        print('result is:', result ["id"])
        db_cursor.close()
        return result


    def close(self):
        self.db_session.close()



