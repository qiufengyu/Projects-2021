#!/usr/bin/python
# coding=utf-8

from flask import Flask, render_template, jsonify
import requests
import jieba
from bs4 import BeautifulSoup
import sqlite3

app = Flask(__name__)
app.config.from_object('config')

login_name = None
login_role = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_analysis')
def search_analysis():
    return render_template('search_analysis.html')

@app.route('/user_guanli')
def user_guanli():
    return render_template('user_guanli.html')

# ------------------ ajax restful api -------------------
@app.route('/check_login')
def check_login():
    """判断用户是否登录"""
    return jsonify({'username': login_name, 'login': login_name is not None, 'role': login_role})


@app.route('/register/<name>/<password>/<role>')
def register(name, password, role):
    conn = sqlite3.connect('user_info.db')
    cursor = conn.cursor()

    check_sql = "SELECT * FROM sqlite_master where type='table' and name='user'"
    cursor.execute(check_sql)
    results = cursor.fetchall()
    # 数据库表不存在
    if len(results) == 0:
        # 创建数据库表
        sql = """
                CREATE TABLE user(
                    name CHAR(256), 
                    password CHAR(256),
                    role CHAR(256)
                );
                """
        cursor.execute(sql)
        conn.commit()
        print('创建数据库表成功！')

    sql = "INSERT INTO user (name, password, role) VALUES (?,?,?);"
    cursor.executemany(sql, [(name, password, role)])
    conn.commit()
    return jsonify({'info': '用户注册成功！', 'status': 'ok'})


@app.route('/login/<name>/<password>/<role>')
def login(name, password, role):
    global login_name, login_role
    conn = sqlite3.connect('user_info.db')
    cursor = conn.cursor()

    check_sql = "SELECT * FROM sqlite_master where type='table' and name='user'"
    cursor.execute(check_sql)
    results = cursor.fetchall()
    # 数据库表不存在
    if len(results) == 0:
        # 创建数据库表
        sql = """
                CREATE TABLE user(
                    name CHAR(256), 
                    password CHAR(256),
                    role CHAR(256)
                );
                """
        cursor.execute(sql)
        conn.commit()
        print('创建数据库表成功！')

    sql = "select * from user where name='{}' and password='{}' and role='{}'".format(name, password, role)
    cursor.execute(sql)
    results = cursor.fetchall()

    if len(results) > 0:
        login_name = name
        login_role = role
        print(results)
        return jsonify({'info': name + '用户登录成功！', 'status': 'ok'})
    else:
        return jsonify({'info': '当前用户不存在或用户角色错误！', 'status': 'error'})


@app.route('/query_all_users')
def query_all_users():
    """获取所有用户"""
    conn = sqlite3.connect('user_info.db')
    cursor = conn.cursor()
    sql = 'select * from user'
    cursor.execute(sql)
    results = cursor.fetchall()
    print(results)
    return jsonify(results)


@app.route('/update_user/<name>/<password>/<role>')
def update_user(name, password, role):
    conn = sqlite3.connect('user_info.db')
    cursor = conn.cursor()
    print((password, role, name))
    sql = "update user set password=?, role=? where name='{}'".format(name)
    print(sql)
    cursor.execute(sql, (password, role))
    conn.commit()
    conn.close()
    return jsonify()


def jaccard_distance(query, title):
    """
    Jaccard distance between the two sequences
    """
    set1, set2 = set(query), set(title)
    return 1 - len(set1 & set2) / float(len(set1 | set2))


def search_product(search):
    search = str(search.encode('gbk')).replace('\\x', '%').replace("'", '').replace(" ", '+')[1:]
    url = 'https://www.gwdang.com/search?crc64=1&s_product={}'.format(search)
    print(url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Cookie': 'index_big_banner=1; __utma=188916852.1831303940.1615802366.1615802366.1615802366.1; __utmc=188916852; __utmz=188916852.1615802366.1.1.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __utmt=1; fp=698a00f7d0517cd020270b30554b5f91; __utmb=188916852.2.10.1615802366; dfp=0H88kUZe0CK+kUt2kUti0H88kUZM0W82EVZM0CcM0W88EVZM0H8QEW88EV3+0UZi0DZ2',
        'Host': 'www.gwdang.com',
        'Referer': 'https://www.gwdang.com/'
    }
    resp = requests.get(url, headers=headers)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'lxml')
    item_list = soup.select('ul.dp-list')[0]
    item_list = item_list.select('li')

    products = []
    for item in item_list:
        try:
            price = item.select('span.price')[0].text.strip()[1:]
            item_title = item.select('a.item-title')[0]
            img_url = item.select('a.item-img')[0].img['data-original']

            item_url = item_title['href']
            item_title = item_title.text.strip()

            site_name = item.select('span.site-name')[0].text
            comment = item.select('span.num')[0].text[:-2]

            item = [item_title, item_url, price, site_name, comment, img_url]
            print(item)
            products.append(item)
        except Exception as e:
            continue

    return products


@app.route('/search/<search_input>')
def search(search_input):
    products = search_product(search_input)[:20]

    prices = []
    comments = []
    wordclout_dict = {}
    for product in products:
        prices.append(product[2])
        comment = product[4]
        if '万' in comment:
            comment = int(float(comment[:-1]) * 10000)
        else:
            comment = int(comment)
        comments.append(comment)

        # 词云分析
        words = jieba.cut(product[3])
        for word in words:
            word = word.strip()
            if word not in wordclout_dict:
                wordclout_dict[word] = 0
            else:
                wordclout_dict[word] += 1

        words = jieba.cut(product[0])
        for word in words:
            word = word.strip()
            if word not in wordclout_dict:
                wordclout_dict[word] = 0
            else:
                wordclout_dict[word] += 1

    wordclout_dict = [(k, wordclout_dict[k]) for k in sorted(wordclout_dict.keys()) if wordclout_dict[k] > 1]
    wordclout_dict = [{"name": k[0], "value": k[1]} for k in wordclout_dict]

    return jsonify({'products': products,
                    'prices': prices,
                    'idx': list(range(len(prices))),
                    'comments': comments,
                    'wordclout_dict': wordclout_dict})


if __name__ == "__main__":
    app.run(host='127.0.0.1')
