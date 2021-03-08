from django.core.paginator import Paginator
from django.shortcuts import render
from snownlp import SnowNLP

from utils.database import DatabaseConnector
from utils.spider import validKeywords

dbUtil = DatabaseConnector(user='root', password='+sknLv5T')

# Create your views here.
def index(request):
    value = ''
    if 'keywords' in request.GET:
        keywords = request.GET.get('keywords', '')
        value = keywords
        items = dbUtil.getByKeywordsIn(keywords)
    else:
        items = dbUtil.getAllOrderByTimestampDesc()
    items.sort(key=lambda item: item['time'], reverse=True)
    # 分页，每页 20 条记录
    paginator = Paginator(items, 20)
    pageNumber = int(request.GET.get('page', default=1))
    pageObj = paginator.get_page(pageNumber)
    return render(request, 'app/index.html', {
        'pageObj': pageObj,
        'inputText': value
    })

def detail(request, id):
    tid = int(id)
    newsItem = dbUtil.getById(tid)
    if newsItem:
        newsItem['summary'] = '。'.join(newsItem['summary'])
        return render(request, 'app/detail.html', context={'item': newsItem})
    return render(request, 'app/detail.html')

def generate(request):
    _content = request.POST.get('content', '')
    keywords = []
    summary = []
    if _content:
        s = SnowNLP(_content)
        # 利用 TextRank 提取最重要的 10 个关键词
        keywords10 = s.keywords(10)
        _keywords = [x for x in keywords10 if (len(x) > 1 and validKeywords(x))]
        keywords = ','.join(_keywords)
        # 生成一个三句话的摘要
        summary = s.summary(3)
        return render(request, 'app/generate.html', context={
            'inputText': _content,
            'keywords': keywords,
            'summary': summary
        })
    return render(request, 'app/generate.html', context={
        'inputText': None,
        'keywords': keywords,
        'summary': summary
    })


