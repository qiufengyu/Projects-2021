# -*- coding: utf-8 -*-
import scrapy
import json
from zhaoping.items import ZhaopingItem


class Job51Spider(scrapy.Spider):
    name = 'job51'
    # 51job招聘网站的入口地址
    allowed_domains = ['51job.com']

    def start_requests(self):
        # 51job网页审查元素后可找到如下获取招聘信息的 api 接口
        base_url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,+,1,{}.html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=0&dibiaoid=0&line=&welfare='

        # 爬取前 100 页的招聘数据
        urls = [base_url.format(page_i) for page_i in range(1, 100)]

        # http 请求头信息
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'Cookie': 'guid=2bcf8fed2bb8221680a46d2a080e627c; nsearch=jobarea%3D%26%7C%26ord_field%3D%26%7C%26recentSearch0%3D%26%7C%26recentSearch1%3D%26%7C%26recentSearch2%3D%26%7C%26recentSearch3%3D%26%7C%26recentSearch4%3D%26%7C%26collapse_expansion%3D; search=jobarea%7E%60000000%7C%21ord_field%7E%600%7C%21recentSearch0%7E%60000000%A1%FB%A1%FA000000%A1%FB%A1%FA0000%A1%FB%A1%FA00%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA1%7C%21collapse_expansion%7E%601%7C%21',
            'Host': 'search.51job.com',
        }
        for url in urls:
            # 抓取当前页
            yield scrapy.Request(url=url, method='GET', callback=self.parse, headers=headers)

    def parse(self, response):
        datas = []
        items = json.loads(response.text)['engine_search_result']

        for item in items:
            try:
                job_item = ZhaopingItem()
                # 提取岗位名称
                job_item['job_name'] = item['job_name']
                # 提取所在行业
                job_item['hangye'] = item['companyind_text']
                # 提取公司名称
                job_item['company'] = item['company_name']
                # 提取薪资
                job_item['salary'] = item['providesalary_text']
                # 提取岗位的属性信息：工作地点
                location = item['attribute_text'][0]
                location = location.split('-')[0]
                location = location.split('_')[0]
                job_item['location'] = location
                # 工作经验要求
                job_item['jingyan'] = item['attribute_text'][1]
                # 学历要求
                job_item['xueli'] = item['attribute_text'][2]
                # 招聘人数
                job_item['zhaopin_counts'] = item['attribute_text'][3]
                # 发布时间
                job_item['pub_time'] = item['issuedate']
                # 返回结果
                yield job_item
            except:
                pass
