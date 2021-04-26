import json
import random
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from snownlp import SnowNLP

ROOT_URL = 'https://feed.mix.sina.com.cn/api/roll/get'

# 爬虫请求头，简单的反(反爬虫)策略
headers = {
    'Content-Type': 'text/html',
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    'Referer': "https://news.sina.com.cn/roll/",
    'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,la;q=0.6",
    'Accept-Encoding': "gzip, deflate, br",
}

category_map = {
    2669: 'SOCIAL',
    2512: 'SPORTS',
    2513: 'ENT',
    2514: 'MIL',
    2515: 'TECH',
    2516: 'FIN'
}


# 访问新闻起始页的请求参数
# lid 代表类别编号：2669 -> 社会，2512 -> 体育，2513 -> 娱乐，2514 -> 军事，2515 -> 科技，2516 -> 财经
def global_params(lid: int, page: int):
    return {
        'pageid': '153',
        'lid': lid,
        'k': '',
        'num': '50',
        'page': page,
        'r': random.random()
    }


# 根据新闻详细内容的链接，获取新闻的正文文本
def request_content(url):
    content = []
    # 打开网页内容
    response = requests.get(url, headers=headers)
    try:
        html_content = response.content.decode('utf-8')
    except UnicodeEncodeError:
        html_content = response.content.decode('gbk')
    soup = BeautifulSoup(html_content, 'lxml')
    # 根据网页 html 元素的标签和 css 样式，获取其中的正文文本
    article = soup.select_one('div.article')
    # 有的新闻网页不太一样，再次尝试获取其中的内容
    if not article:
        article = soup.select_one('div#artibody')
    elif not article:
        article = soup.select_one('div#article')
    paras = article.select('p')
    if paras:
        for para in paras:
            line = para.text.strip()
            if len(line) >= 1:
                content.append(line)
    return content


# 根据起始页和中止页，获取新闻内容
def request_roll(category: int, startPage: int, endPage: int):
    category_prefix = category_map[category]
    file_out = '../data/' + category_prefix + '.txt'
    with open(file_out, 'a', encoding='utf-8') as fw:
        count = 0
        for i in range(startPage, endPage):
            try:
                # 打开网页，获取网页内容
                response = requests.get(ROOT_URL, params=global_params(category, i), headers=headers)
                if response.status_code == 200:
                    # 网页为 gbk 编码，需要进行转码
                    gbk_content = response.content.decode('gbk')
                    j = json.loads(gbk_content)
                    data = j['result']['data']
                    for d in data:
                        title = d['title']  # 标题
                        url = d['url']  # 新闻链接
                        print(title, '-> 获取新闻内容')
                        _content = request_content(url)
                        if len(_content) > 0:
                            content = '\n'.join(_content)
                            # SnowNLP 这个库中的关键词提取、摘要提取就是用的 TextRank 算法
                            # 论文中可以详细介绍这一算法：http://www.hankcs.com/nlp/textrank-algorithm-java-implementation-of-automatic-abstract.html
                            # 主要思路：分词后根据句子中的词，计算出每个句子的一个向量表示，根据相邻句子对当前句子的"贡献"，以相似度为权重，计算当前句子的重要程度，最重要的句子即为摘要
                            s = SnowNLP(content)
                            # 生成一个三句话的摘要
                            _summary = s.summary(3)
                            # 写入对应的文件中
                            fw.write(' '.join(_summary) + '\n')
                            fw.flush()
                            count += 1
                            if count % 10 == 0:
                                print('=========', count, category_prefix + '新闻已保存')
                        else:
                            print('当前新闻网页格式特殊，未能成功解析，跳过')
                        # 暂停一下，避免爬虫太频繁
                        time.sleep(random.random() * 5.0)
            except requests.RequestException:
                # 爬虫程序无法获取网页内容
                print('Cannot get response')
            # 每一组也暂停 30s
            time.sleep(30)


# 爬虫程序，获取每一类别新闻的摘要
if __name__ == '__main__':
    for category in category_map:
        request_roll(category, 1, 2)
        time.sleep(random.random() * 60.0)
