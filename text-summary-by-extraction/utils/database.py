import re

import mysql.connector
from mysql.connector import IntegrityError

insertSQL = """INSERT INTO `TEXT_SUMMARY` (`title`, `content`, `keywords`, `summary`, `url`, `newsTimestamp`) values
            (%(title)s, %(content)s, %(keywords)s, %(summary)s, %(url)s, %(newsTimestamp)s)
"""

# 数据库链接的类，支持插入、查询等功能
class DatabaseConnector:
    def __init__(self, user, password, database='news'):
        """
        初始化数据库链接
        :param user: 用户名
        :param password: 密码
        :param database: schema/database 的名字
        """
        self.cnx = mysql.connector.connect(user=user, password=password,
                              host='localhost', database=database,
                              use_pure=False)

    def __del__(self):
        self.cnx.close()

    # 根据所有新闻的时间倒序排序
    def getAllOrderByTimestampDesc(self):
        result = []
        query = """SELECT id AS tid, title, keywords, summary, newsTimestamp FROM TEXT_SUMMARY ORDER BY newsTimestamp DESC"""
        with self.cnx.cursor() as cursor:
            cursor.execute(query)
            for (tid, title, keywords, summary, newsTimestamp) in cursor:
                result.append({
                    'id': tid,
                    'title': title,
                    'keywords': keywords,
                    'time': newsTimestamp.strftime('%Y-%m-%d %H:%M')
                })
            return result

    # 根据新闻的 id （数据库自增主键）获取完整内容
    def getById(self, tid):
        result = {}
        query = """SELECT id AS tid, title, url, keywords, summary, content, newsTimestamp FROM TEXT_SUMMARY WHERE id = %(id)s"""
        with self.cnx.cursor() as cursor:
            cursor.execute(query, {'id': tid})
            r = cursor.fetchone()
            if r:
                result['id'] = r[0]
                result['title'] = r[1]
                result['url'] = r[2]
                result['keywords'] = r[3]
                result['summary'] = r[4].split('|')
                result['content'] = r[5].decode('utf-8').split('\n')
                result['time'] = r[6].strftime('%Y-%m-%d %H:%M')
        return result

    # 根据关键词搜索相关的新闻
    def getByKeywordsIn(self, keywords):
        query = """SELECT id AS tid, title, keywords, summary, newsTimestamp FROM TEXT_SUMMARY WHERE keywords LIKE %(pattern)s"""
        _results = []
        with self.cnx.cursor() as cursor:
            if keywords:
                for kw in re.split(r'[,\W，]', keywords):
                    cursor.execute(query, {'pattern': '%' + kw + '%'})
                    for (tid, title, keywords, summary, newsTimestamp) in cursor:
                        _results.append({
                            'id': tid,
                            'title': title,
                            'keywords': keywords,
                            'time': newsTimestamp.strftime('%Y-%m-%d %H:%M')
                        })
        result = list({v['id']: v for v in _results}.values())
        return result

    # 将一条新闻插入数据库中
    def insertOne(self, title, content, keywords, summary, url, time):
        with self.cnx.cursor() as cursor:
            try:
                cursor.execute(insertSQL, {'title': title,
                                           'content': content,
                                           'keywords': keywords,
                                           'summary': summary,
                                           'url': url,
                                           'newsTimestamp': time})
                self.cnx.commit()
                print(title, '-> 成功保存')
            except IntegrityError:
                print(title, '-> 本文已在数据库中，不再处理')

if __name__ == '__main__':
    conn = DatabaseConnector(user='root', password='+sknLv5T')
    result = conn.getByKeywordsIn('美元 中国')
    for r in result:
        print(r)


