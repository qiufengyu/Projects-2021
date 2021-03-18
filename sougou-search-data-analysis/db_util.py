from urllib.parse import urlparse
from datetime import datetime

import mysql.connector
from typing import List

SELECT_USER_BY_INITIALID = """
    SELECT u.uid FROM web.user u where u.initialid = %s
"""

INSERT_USER = """
    INSERT INTO web.user (initialid) VALUES (%s)
"""

INSERT_USER_SEARCH = """
    INSERT INTO web.user_search (uid, query) VALUES (%s, %s)
"""

INSERT_USER_TIME = """
    INSERT INTO web.user_time (uid, timeminutes) VALUES (%s, %s)
"""

INSERT_USER_URL = """
    INSERT INTO web.user_url (uid, url) VALUES (%s, %s)
"""

SEARCH_VOLUMN_SQL = """
    select u.initialid, us.ucount
    from web.user u
    inner join
    (select us.uid, count(*) as ucount from web.user_search us group by us.uid order by ucount desc LIMIT %s) as us
    on u.uid = us.uid;
"""

SEARCH_QUERY_SQL = """
    select us.query
    from web.user_search us inner join web.user u on us.uid = u.uid
    where u.initialid = %s
"""

SEARCH_TIME_SQL = """
    select ut.timeminutes
    from web.user_time ut inner join web.user u on u.uid = ut.uid
    where u.initialid = %s

"""

SEARCH_URL_SQL = """
    select uu.url, count(*) as ucount
    from web.user_url uu inner join web.user u on u.uid = uu.uid
    where u.initialid = %s
    group by uu.url order by ucount desc;
"""

SEARCH_KEYWORD_SQL = """
    select us.uid, u.initialid, count(*) as scount
    from web.user_search us join web.user u on u.uid = us.uid
    where us.query like %s group by u.uid, u.initialid order by scount desc;
"""


class DBUtil:
    def __init__(self):
        self.cnx = mysql.connector.connect(user='root', password='root',
                                           host='localhost',
                                           database='web')

    # def __del__(self):
    #     self.cnx.commit()
    #     self.cnx.close()

    def clean(self):
        # 将现有数据全部删除
        cursor = self.cnx.cursor()
        cursor.execute('DELETE FROM web.user_search')
        self.cnx.commit()
        cursor.execute('DELETE FROM web.user_time')
        self.cnx.commit()
        cursor.execute('DELETE FROM web.user_url')
        self.cnx.commit()
        cursor.execute('DELETE FROM web.user')
        self.cnx.commit()

    def insert_user(self, initial_id: str) -> int:
        cursor = self.cnx.cursor()
        cursor.execute(SELECT_USER_BY_INITIALID, (initial_id,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(INSERT_USER, (initial_id,))
            self.cnx.commit()
        cursor.execute(SELECT_USER_BY_INITIALID, (initial_id,))
        row = cursor.fetchone()
        return row[0]

    def insert_user_search(self, uid: int, query: str):
        cursor = self.cnx.cursor()
        # 把原本的方括号去掉
        query = query[1:-1]
        if query and len(query) < 255:
            cursor.execute(INSERT_USER_SEARCH, (uid, query))

    def insert_user_time(self, uid: int, time_str: str):
        cursor = self.cnx.cursor()
        time_parts = time_str.split(':')
        # 记为分钟数
        time_minutes = int(int(time_parts[0]) * 60 + int(time_parts[1]))
        cursor.execute(INSERT_USER_TIME, (uid, time_minutes))

    def insert_user_url(self, uid: int, url: str):
        cursor = self.cnx.cursor()
        if not url.startswith('http://'):
            url = 'http://' + url
        # 只保留网站的域名
        host = urlparse(url).netloc
        cursor.execute(INSERT_USER_URL, (uid, host))

    def process_one_line(self, line: str):
        parts = line.split('\t')
        if len(parts) == 5:
            time_str, initial_id, query, url = parts[0], parts[1], parts[2], parts[-1]
            uid = self.insert_user(initial_id)
            self.insert_user_search(uid, query)
            self.insert_user_time(uid, time_str)
            self.insert_user_url(uid, url)

    def read_file(self, file_name: str):
        count = 0
        with open(file_name, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    count += 1
                    self.process_one_line(line)
                    if count % 2500 == 0:
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        self.cnx.commit()
                        print(current_time, count, 'records saved...')

    def select_top_search_volume(self, limit=20):
        results = []
        cursor = self.cnx.cursor()
        cursor.execute(SEARCH_VOLUMN_SQL, (limit,))
        for r in cursor:
            result = {}
            result['initialid'] = r[0]
            result['count'] = int(r[1])
            results.append(result)
        return results

    def select_search_query(self, uiid: str):
        results = []
        cursor = self.cnx.cursor()
        cursor.execute(SEARCH_QUERY_SQL, (uiid,))
        for q in cursor:
            results.append(q[0])
        return results

    def select_user_time(self, uiid: str):
        results: List[int] = []
        cursor = self.cnx.cursor()
        cursor.execute(SEARCH_TIME_SQL, (uiid,))
        for q in cursor:
            m = int(q[0]) // 60
            results.append(m)
        return results

    def select_user_url(self, uiid: str):
        results = []
        cursor = self.cnx.cursor()
        cursor.execute(SEARCH_URL_SQL, (uiid,))
        for q in cursor:
            results.append({'name': q[0], 'value': int(q[1])})
        return results

    def select_keyword(self, kw: str):
        results = []
        cursor = self.cnx.cursor()
        param = '%' + kw + '%'
        cursor.execute(SEARCH_KEYWORD_SQL, (param,))
        for r in cursor:
            results.append({'uiid': r[1], 'count': int(r[2])})
        return results


# 这里用的文件是样例，需要自己去 https://www.sogou.com/labs/resource/q.php
# 下载对应的文件，并且解压出来，纯文本模式，放在 data 文件夹下，同时修改下面代码的文件名
if __name__ == '__main__':
    db_util = DBUtil()
    # 如果想要重置数据库，需要执行 clean
    # db_util.clean()
    db_util.read_file('data/sogouQ.10.reduced')
