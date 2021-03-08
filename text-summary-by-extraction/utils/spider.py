import json
import random
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from snownlp import SnowNLP

from utils.database import DatabaseConnector

# 请求新闻列表的原始 URL 入口
# 新闻起始页入口的 API，在浏览器请求中可以得到该 API
# 不需要解析起始页 https://news.sina.com.cn/roll/ 上的新闻了
rootURL = 'https://feed.mix.sina.com.cn/api/roll/get'

# 爬虫请求头，简单的反-反爬虫策略
headers = {
    'Content-Type': 'text/html',
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    'Referer': "https://news.sina.com.cn/roll/",
    'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,la;q=0.6",
    'Accept-Encoding': "gzip, deflate, br",
}

# 访问新闻起始页的请求参数
def globalParams(page):
    return {
        'pageid': '153',
        'lid': '2509',
        'k': '',
        'num': '50',
        'page': page,
        'r': random.random()
    }

# 根据新闻详细内容的链接，获取新闻的正文文本
def requestContent(url):
    content = []
    # 打开网页内容
    response = requests.get(url, headers=headers)
    try:
        htmlContent = response.content.decode('utf-8')
    except:
        htmlContent = response.content.decode('gbk')
    soup = BeautifulSoup(htmlContent, 'html.parser')
    # 根据网页 html 元素的标签和 css 样式，获取其中的正文文本
    article = soup.select_one('div.article')
    if not article:
        article = soup.select_one('div#artibody')
    paras = article.select('p')
    if paras:
        for para in paras:
            line = para.text.strip()
            if len(line) >= 1:
                content.append(line)
    return content

# 根据起始页和中止页，获取新闻内容
def requestSina(startPage, endPage):
    # 数据库链接，填入你的 mysql 数据库用户名和密码
    dbUtil = DatabaseConnector(user='root', password='+sknLv5T')
    for i in range(startPage, endPage):
        try:
            # 打开网页，获取网页内容
            response = requests.get(rootURL, params=globalParams(i), headers=headers)
            if response.status_code == 200:
                # 网页为 gbk 编码，需要进行转码
                gbkContent = response.content.decode('gbk')
                j = json.loads(gbkContent)
                data = j['result']['data']
                for d in data:
                    title = d['title'] # 标题
                    url = d['url'] # 新闻链接
                    keywords = d['keywords'] # 关键词（如有，没有的话也用 TextRank 算法提取）
                    ctime = datetime.fromtimestamp(int(d['ctime'])) # 新闻时间
                    print(title, '-> 获取新闻内容')
                    _content = requestContent(url)
                    content = '' # 新闻正文
                    if len(_content) > 0:
                        content = '\n'.join(_content)
                        # ！！！SnowNLP 这个库中的关键词提取、摘要提取就是用的 TextRank 算法
                        # 论文中可以详细介绍这一算法：http://www.hankcs.com/nlp/textrank-algorithm-java-implementation-of-automatic-abstract.html
                        # 主要思路：分词后根据句子中的词，计算出每个句子的一个向量表示，根据相邻句子对当前句子的"贡献"，以相似度为权重，计算当前句子的重要程度，最重要的句子即为摘要
                        s = SnowNLP(content)
                        # 利用 TextRank 提取最重要的 10 个关键词
                        keywords10 = s.keywords(10)
                        _keywords = [x for x in keywords10 if (len(x) > 1 and validKeywords(x))]
                        if not keywords:
                            keywords = ','.join(_keywords)
                        # 生成一个三句话的摘要
                        _summary = s.summary(3)
                        summary = '|'.join(_summary)
                        # 写入数据库，供查询展示
                        dbUtil.insertOne(title, content, keywords, summary, url, ctime)
                        # 暂停一下，避免爬虫太频繁
                        time.sleep(random.random() * 10.0)
        except requests.RequestException:
            # 爬虫程序无法获取网页内容
            print('Cannot get or response')
        # 每一组也暂停 30s
        time.sleep(30)

# 中文标点不认为是关键词
def validKeywords(x):
    if ('—' in x) or ('：') in x or ('"' in x) or \
            ('，' in x) or ('。' in x) or (x.isdigit()):
        return False
    else:
        return True

# 爬虫程序，获取第 [1,3) 页的新闻
if __name__ == '__main__':
    requestSina(1, 6)
