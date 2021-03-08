import json
import pprint
import random
import sys
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


# https://m.weibo.cn/api/feed/trendtop?containerid=102803_ctg1_8999_-_ctg1_8999_home
# https://m.weibo.cn/statuses/extend?id=4609497655937030
# https://m.weibo.cn/api/container/getIndex?containerid=102803&openApp=0
# https://m.weibo.cn/status/
import data_util
from lstm import SemiLSTM

my_headers = {
    ':authority': 'm.weibo.cn',
    ':method': 'GET',
    ':path': '/api/feed/trendtop?containerid=102803_ctg1_8999_-_ctg1_8999_home',
    ':scheme': 'https',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,la;q=0.6',
    'cookie': 'WEIBOCN_FROM=1110006030',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
}

class WeiboSpider:
    def __init__(self, data_util, saved_lstm):
        self.name = 'WeiboSpider'
        self.url = 'https://d.weibo.com/'
        self.m_url = 'https://m.weibo.cn'
        self.status_url = 'https://m.weibo.cn/status/'
        self.data_util = data_util
        self.lstm = saved_lstm

    def config_driver(self):
        # 这里使用 Chrome 浏览器，其他的推荐 Firefox 之类的
        # 去 https://sites.google.com/a/chromium.org/chromedriver/ 下载最新版即可（翻墙）
        # 360、QQ、sougou 之类的如果有对应的驱动也可以，但最好别用
        # window 环境，保持现在的配置即可
        # macOS 则需要指定 chromedriver 路径
        if sys.platform.lower().startswith('win'):
            # 这里附了一个可用的 windows 平台的驱动
            self.driver = webdriver.Chrome('./chromedriver')
        elif sys.platform.lower().startswith('darwin'):
            # macOS 指定驱动的路径
            self.driver = webdriver.Chrome('/usr/local/bin/chromedriver')
        else:
            print("Not supported platform")
            exit(-1)
        self.driver.set_page_load_timeout(1000)

    def parse(self, pages=1):
        self.config_driver()
        print("Open driver...")
        with open('weibo_result.txt', 'a', encoding='utf-8') as f_result:
            for p in range(pages):
                page = p + 1
                self.driver.get('https://m.weibo.cn/api/feed/trendtop?containerid=102803&page=' + str(page))
                main_window = self.driver.current_window_handle
                json_response_text = self.driver.find_element_by_tag_name('pre').text
                json_object = json.loads(json_response_text)
                # pprint.pprint(json_object)
                cards = json_object['data']['cards']
                for card in cards:
                    weibo_id = card['mblog']['mid']
                    # open new blank tab
                    self.driver.execute_script("window.open();")
                    # switch to the new window which is second in window_handles array
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    # open successfully and close
                    self.driver.get(self.status_url + str(weibo_id))
                    print('获取微博 id =', weibo_id)
                    weibo_response_source = self.driver.page_source
                    html = BeautifulSoup(weibo_response_source, 'lxml')
                    scripts = html.find_all('script')
                    if len(scripts) > 0:
                        for script in scripts:
                            script_text = script.string
                            if script_text and '$render_data' in script_text:
                                second_part = script_text.split('$render_data')[1][3:]
                                render_data = second_part.split('[0] || {};')[0]
                                render_data_json_object = json.loads(render_data)
                                status = render_data_json_object[0]['status']
                                created_at = status['created_at']
                                id = status['id']
                                _text = status['text']
                                weibo_text = BeautifulSoup(_text, 'lxml').text
                                weibo_text = weibo_text.replace('#', '')
                                feature = self.data_util.extract_feature(weibo_text)
                                result = self.lstm.test_text(feature, saved_model='my-lstm')
                                user = status['user']
                                user_id = user['id']
                                user_screen_name = user['screen_name']
                                print('测试样例 {}： {}（{}） @ {}：{}。\n测试结果：{}'.format(id, user_screen_name, user_id, created_at, weibo_text, result))
                                f_result.write('测试样例 {}： {} @ {}：{}。测试结果：{}\n'.format(id, user_screen_name, created_at, weibo_text, result))
                                # pprint.pprint(render_data_json_object)
                    else:
                        print('本次爬虫被新浪微博阻止，探查失败，跳过。等待一段时间后，尝试下一个')

                    time.sleep((10 * random.random() + 5))
                    print('=' * 80)
                    self.driver.close()
                    self.driver.switch_to.window(main_window)
                f_result.flush()
                time.sleep((10 * random.random() + 10))
        self.driver.quit()



if __name__ == '__main__':
    data_util = data_util.DataUtil()
    saved_lstm = SemiLSTM(lr=1e-4, epochs=20, batch_size=50)
    weibo_spider = WeiboSpider(data_util, saved_lstm)
    weibo_spider.parse(pages=3)