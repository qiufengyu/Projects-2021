#!/usr/bin/python
# _*_ coding: utf-8 _*_

"""
前程无忧全国招聘信息爬虫
"""
import time
import sqlite3
import requests

# 判断是否存在数据库，不存在则创建
conn = sqlite3.connect('job_info.db')
cursor = conn.cursor()

check_sql = "SELECT * FROM sqlite_master where type='table' and name='job'"
cursor.execute(check_sql)
results = cursor.fetchall()
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
    cursor.execute(sql)
    conn.commit()
    print('创建数据库表成功！')

# 前程无忧招聘网站，一共包含 2000 页
total_page = 100

# 爬取错误的页面
error_pages = []

base_url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,+,1,{}.html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=0&dibiaoid=0&line=&welfare='
datas = []
for page in range(1, total_page + 1):
    print('--> 爬取第 {} 页'.format(page))
    url = base_url.format(page)
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'Cookie': 'guid=2bcf8fed2bb8221680a46d2a080e627c; nsearch=jobarea%3D%26%7C%26ord_field%3D%26%7C%26recentSearch0%3D%26%7C%26recentSearch1%3D%26%7C%26recentSearch2%3D%26%7C%26recentSearch3%3D%26%7C%26recentSearch4%3D%26%7C%26collapse_expansion%3D; search=jobarea%7E%60000000%7C%21ord_field%7E%600%7C%21recentSearch0%7E%60000000%A1%FB%A1%FA000000%A1%FB%A1%FA0000%A1%FB%A1%FA00%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA1%7C%21collapse_expansion%7E%601%7C%21',
        'Host': 'search.51job.com',
    }
    response = requests.get(url, headers=headers)
    items = response.json()['engine_search_result']

    for item in items:
        try:
            job_name = item['job_name']
            hangye = item['companyind_text']
            company = item['company_name']
            salary = item['providesalary_text']

            location = item['attribute_text'][0]
            location = location.split('-')[0]
            location = location.split('_')[0]

            jingyan = item['attribute_text'][1]
            xueli = item['attribute_text'][2]
            zhaopin_counts = item['attribute_text'][3]
            pub_time = item['issuedate']
            datas.append((job_name, hangye, company, location, salary, jingyan, xueli, zhaopin_counts, pub_time))
        except:
            pass

    print('爬取了 {} 条就业数据'.format(len(datas)))

    insert_sql = "INSERT INTO job(job_name, hangye, company, location, salary, jingyan, xueli, zhaopin_counts, pub_time) VALUES (?,?,?,?,?,?,?,?,?);"
    cursor.executemany(insert_sql, datas)
    conn.commit()
    time.sleep(1)
