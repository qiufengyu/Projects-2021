#!/usr/bin/python
# _*_ coding: utf-8 _*_

"""
爬虫测试代码
"""
import requests
from bs4 import BeautifulSoup


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


search_product('金龙鱼')
