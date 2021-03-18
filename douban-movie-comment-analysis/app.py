#!/usr/bin/python
# coding=utf-8

import re
import json
import sqlite3
from flask import Flask, render_template, jsonify
import requests
import execjs
from bs4 import BeautifulSoup
from snownlp import SnowNLP
import random
import jieba
from jieba.analyse.tfidf import TFIDF
from collections import Counter

# 中文停用词
STOPWORDS = set(map(lambda x: x.strip(), open('../../Desktop/MovieCommentAnalysis/stopwords.txt', encoding='utf-8').readlines()))

app = Flask(__name__)
app.config.from_object('config')
execjs.runtimes = 'Node'

headers = {
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    'accept-language': "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
    'cookie': 'll="108296"; bid=ieDyF9S_Pvo; __utma=30149280.1219785301.1576592769.1576592769.1576592769.1; __utmc=30149280; __utmz=30149280.1576592769.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _vwo_uuid_v2=DF618B52A6E9245858190AA370A98D7E4|0b4d39fcf413bf2c3e364ddad81e6a76; ct=y; dbcl2="40219042:K/CjqllYI3Y"; ck=FsDX; push_noty_num=0; push_doumail_num=0; douban-fav-remind=1; ap_v=0,6.0',
    'host': "search.douban.com",
    'referer': "https://movie.douban.com/",
    'sec-fetch-mode': "navigate",
    'sec-fetch-site': "same-site",
    'sec-fetch-user': "?1",
    'upgrade-insecure-requests': "1",
    'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.56"
}

login_name = None


class WordSegmentPOSKeywordExtractor(TFIDF):

    def extract_sentence(self, sentence, keyword_ratios=None):
        """
        Extract keywords from sentence using TF-IDF algorithm.
        Parameter:
            - keyword_ratios: return how many top keywords. `None` for all possible words.
        """
        words = self.postokenizer.cut(sentence)
        freq = {}

        seg_words = []
        pos_words = []
        for w in words:
            wc = w.word
            seg_words.append(wc)
            pos_words.append(w.flag)

            if len(wc.strip()) < 2 or wc.lower() in self.stop_words:
                continue
            freq[wc] = freq.get(wc, 0.0) + 1.0

        if keyword_ratios is not None and keyword_ratios > 0:
            total = sum(freq.values())
            for k in freq:
                freq[k] *= self.idf_freq.get(k, self.median_idf) / total

            tags = sorted(freq, key=freq.__getitem__, reverse=True)
            top_k = int(keyword_ratios * len(seg_words))
            tags = tags[:top_k]

            key_words = [int(word in tags) for word in seg_words]

            return seg_words, pos_words, key_words
        else:
            return seg_words, pos_words


extractor = WordSegmentPOSKeywordExtractor()


def fetch_keywords(new_title):
    """新闻关键词抽取，保留表征能力强名词和动词"""
    seg_words, pos_words, key_words = extractor.extract_sentence(new_title, keyword_ratios=0.8)
    seg_key_words = []
    for word, pos, is_key in zip(seg_words, pos_words, key_words):
        if pos in {'n', 'nt', 'nd', 'nl', 'nh', 'ns', 'nn', 'ni', 'nz', 'v', 'vd', 'vl', 'vu', 'a'} and is_key:
            if word not in STOPWORDS:
                seg_key_words.append(word)

    return seg_key_words


# --------------------- html render ---------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

# ------------------ ajax restful api -------------------
@app.route('/check_login')
def check_login():
    """判断用户是否登录"""
    return jsonify({'username': login_name, 'login': login_name is not None})


@app.route('/register/<name>/<password>')
def register(name, password):
    conn = sqlite3.connect('../../Desktop/MovieCommentAnalysis/user_info.db')
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
                    password CHAR(256)
                );
                """
        cursor.execute(sql)
        conn.commit()
        print('创建数据库表成功！')

    sql = "INSERT INTO user (name, password) VALUES (?,?);"
    cursor.executemany(sql, [(name, password)])
    conn.commit()
    return jsonify({'info': '用户注册成功！', 'status': 'ok'})


@app.route('/login/<name>/<password>')
def login(name, password):
    global login_name
    conn = sqlite3.connect('../../Desktop/MovieCommentAnalysis/user_info.db')
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
                    password CHAR(256)
                );
                """
        cursor.execute(sql)
        conn.commit()
        print('创建数据库表成功！')

    sql = "select * from user where name='{}' and password='{}'".format(name, password)
    cursor.execute(sql)
    results = cursor.fetchall()

    login_name = name
    if len(results) > 0:
        print(results)
        return jsonify({'info': name + '用户登录成功！', 'status': 'ok'})
    else:
        return jsonify({'info': '当前用户不存在！', 'status': 'error'})


def request_from(url):
    resp = requests.get(url, headers=headers)
    resp.encoding = 'gbk'
    html = re.search('window.__DATA__ = "([^"]+)"', resp.text).group(1)

    with open('../../Desktop/MovieCommentAnalysis/main.js', 'r') as f:
        decrypt_js = f.read()
    ctx = execjs.compile(decrypt_js)
    data = ctx.call('decrypt', html)
    return data


# remove space
spaces = {'\x10', '\x7f', '\x9d', '\xad', '\\x0a', '\\xa0', '\\x0d',
          '\f', '\n', '\r', '\t', '\v', '&#160;', '&nbsp;',
          '\u200b', '\u200e', '\u202a', '\u202c', '\ufeff', '\uf0d8', '\u2061', '\u1680', '\u180e',
          '\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', '\u2008',
          '\u2009', '\u200a', '\u2028', '\u2029', '\u202f', '\u205f', '\u3000'}


def remove_space(text):
    for space in spaces:
        text = text.replace(space, '')
    text = text.strip()
    text = re.sub('\s+', ' ', text)
    return text


def clean_duplacte_words(text):
    """
    去除很多重复的词和标点符号
    """
    reg = r'([^0-9IX]+)(\1){2,}'
    for i in range(6):
        temp = text
        text = re.sub(reg, lambda m: m.group(1), text)
        if len(text) == len(temp):
            break
    return text


@app.route('/movie_search/<movie_name>')
def movie_search(movie_name):
    """电影搜索"""
    print('=======> 搜索电影：', movie_name)
    url = 'https://search.douban.com/movie/subject_search?search_text={}&cat=1002'.format(movie_name)
    response = request_from(url)
    print(json.dumps(response, ensure_ascii=False))
    movie_info = response['payload']['items'][0]

    movie_img = movie_info['cover_url']
    movie_abstract_tags = movie_info['abstract']
    movie_actors = movie_info['abstract_2']
    movie_title = movie_info['title']
    movie_url = movie_info['url']

    clean_headers = {
        'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.56"
    }
    print(movie_url)
    comment_url = movie_url
    response = requests.get(comment_url, headers=clean_headers)
    response.encoding = 'utf8'
    response = response.text
    soup = BeautifulSoup(response, 'lxml')
    comment_divs = soup.select('div.review-item')

    movie_intro = soup.find('span', attrs={'property': 'v:summary'}).text.strip()
    movie_intro = remove_space(movie_intro)
    movie_intro = clean_duplacte_words(movie_intro)

    # 豆瓣评分
    douban_score = soup.select('strong.ll.rating_num')[0].text
    douban_score = float(douban_score)

    comments = set()
    # 评论关键词
    all_keywords = []
    # 淘票票评论
    for comment_div in comment_divs:
        com_time = comment_div.find('span', class_='main-meta').text
        comment = re.sub(r'\s+', '', comment_div.find('div', class_='short-content').text.strip()).replace('...(展开)', '')
        comment = remove_space(comment)
        comment = clean_duplacte_words(comment)
        # 评论情感分析
        postive_score = SnowNLP(comment).sentiments
        # 评论日期
        com_time = com_time.strip().split(' ')[0]
        # 评论分词
        comment = ' '.join(jieba.cut(comment))
        keywords = fetch_keywords(comment)
        all_keywords.extend(keywords)
        comments.add((comment, com_time, postive_score))

    count = 0
    while 0 < len(comments) < 100:
        if count > 4:
            break
        start = 10 * (len(comments) // 10 + 1)
        comment_url = movie_url + '/reviews?start={}'.format(start)
        response = requests.get(comment_url, headers=clean_headers)
        response.encoding = 'utf8'
        response = response.text
        soup = BeautifulSoup(response, 'lxml')
        comment_divs = soup.select('div.review-item')
        count += 1
        for comment_div in comment_divs:
            com_time = comment_div.find('span', class_='main-meta').text
            comment = re.sub(r'\s+', '', comment_div.find('div', class_='short-content').text.strip()).replace(
                '...(展开)', '')
            if len(comments) < 100:
                # 评论情感分析
                postive_score = SnowNLP(comment).sentiments
                # 评论日期
                com_time = com_time.strip().split(' ')[0]
                # 评论分词
                comment = ' '.join(jieba.cut(comment))
                keywords = fetch_keywords(comment)
                all_keywords.extend(keywords)
                comments.add((comment, com_time, postive_score))
            else:
                break
        start += 10
    comments = list(comments)
    print('评论个数：', len(comments))
    # 电影海报
    if movie_img.endswith('webp'):
        url = 'https://www.1905.com/search/?q={}'.format(movie_title)
        cate_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        }
        response = requests.get(url, headers=cate_headers)
        response.encoding = 'utf8'
        response = response.text
        soup = BeautifulSoup(response, 'lxml')
        movie_img = soup.select('div.movie-pic')[0]
        movie_img = movie_img.find('img')['src']

    date_scores = []
    wordclout_dict = {}
    for data in comments:
        comment_keywords, date, score = data[0], data[1], data[2]
        date_scores.append(score)

        words = comment_keywords.split(' ')
        for word in words:
            word = word.strip()
            # 去除停用词
            if word in STOPWORDS or word in movie_title:
                continue

            if word not in wordclout_dict:
                wordclout_dict[word] = 0
            else:
                wordclout_dict[word] += 1

    # 计算这天的评分均值
    wordclout_dict = [(k, wordclout_dict[k]) for k in sorted(wordclout_dict.keys()) if wordclout_dict[k] > 1]
    wordclout_dict = [{"name": k[0], "value": k[1]} for k in wordclout_dict]
    random.shuffle(date_scores)

    print(comments)
    print(comments[0])
    print('电影名称：', movie_title)
    print('电影海报：', movie_img)
    print('电影标签：', movie_abstract_tags)
    print('电影演员：', movie_actors)
    print('电影简介：', movie_intro)
    print('电影链接：', movie_url)
    print('电影评论：', len(comments))
    print('豆瓣评分：', douban_score)

    # 关键词次数统计
    keyword_counts = Counter(all_keywords)
    keyword_counts = keyword_counts.most_common()[:30]
    keywords = [k[0] for k in keyword_counts]
    counts = [k[1] for k in keyword_counts]

    # 情感加权评分
    mean_score = sum(date_scores) / len(date_scores)
    # 转换为豆瓣评分的 10 分制
    mean_score = 100 * mean_score / 11

    return jsonify({'msg': 'success',
                    '电影海报': movie_img,
                    '电影标签': movie_abstract_tags,
                    '电影演员': movie_actors,
                    '电影简介': movie_intro,
                    '电影名称': movie_title,
                    '评分': date_scores,
                    '评分id': list(range(len(date_scores))),
                    '词云数据': wordclout_dict,
                    '属性词': keywords,
                    '属性词次数': counts,
                    '豆瓣评分': douban_score,
                    '预测情感评分': mean_score
                    })


if __name__ == "__main__":
    app.run(host='127.0.0.1')
