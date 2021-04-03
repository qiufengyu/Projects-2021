#!/usr/bin/python
# _*_ coding: utf-8 _*_

"""
地理分区爬虫
"""
import json
import requests
from bs4 import BeautifulSoup

url = 'http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2019/'
response = requests.get(url)
response.encoding = 'gbk'
soup = BeautifulSoup(response.text, 'lxml')
province_trs = soup.find_all('tr', class_='provincetr')


shengfen_city_dict = {}

for province_tr in province_trs:
    shengfen_tds = province_tr.find_all('td')
    for td in shengfen_tds:
        shengfen = td.text.strip()
        if shengfen == '':
            break
        print(shengfen)
        shengfen_city_dict[shengfen] = []
        href = url + td.a['href']
        response = requests.get(href)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, 'lxml')
        cities = soup.find_all('tr', class_='citytr')
        for city in cities:
            city = city.select('td')[1].text.strip()
            if city == '市辖区':
                city = shengfen
            shengfen_city_dict[shengfen].append(city)

print(shengfen_city_dict)
json.dump(shengfen_city_dict, open('dili_fenqu.json', 'w', encoding='utf8'), ensure_ascii=False)
