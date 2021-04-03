# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3
import time


class ZhaopingPipeline(object):

    def __init__(self):
        # 判断是否存在数据库，不存在则创建
        self.conn = sqlite3.connect('../JobAnalysis/job_info.db')
        self.cursor = self.conn.cursor()

        check_sql = "SELECT * FROM sqlite_master where type='table' and name='job'"
        self.cursor.execute(check_sql)
        results = self.cursor.fetchall()
        # 数据库表不存在
        if len(results) == 0:
            # 创建数据库表
            sql = """
                    CREATE TABLE job(
                        job_name CHAR(256),
                        hangye CHAR(256),
                        company CHAR(256),
                        location CHAR(64),
                        salary CHAR(64),
                        jingyan CHAR(64),
                        xueli CHAR(64),
                        zhaopin_counts CHAR(64),
                        pub_time CHAR(256)
                    );
                    """
            self.cursor.execute(sql)
            self.conn.commit()
            print('创建数据库表成功！')


    def process_item(self, item, spider):
        insert_sql = "INSERT INTO job(job_name, hangye, company, location, salary, jingyan, xueli, zhaopin_counts, pub_time) VALUES (?,?,?,?,?,?,?,?,?);"
        datas = [[item['job_name'], item['hangye'], item['company'], item['location'], item['salary'],
                 item['jingyan'], item['xueli'], item['zhaopin_counts'], item['pub_time']]]
        self.cursor.executemany(insert_sql, datas)
        self.conn.commit()
        return item
