import json
from collections import Counter

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

# Create your views here.
import jieba
from db_util import DBUtil

# 初始化数据库对象
db_util = DBUtil()


# 登录
# user 1234
# test 1234
def my_login(request):
    context = {}
    if request.method == 'POST':
        username = str(request.POST['usernameInput']).strip()
        password = str(request.POST['passwordInput']).strip()
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            context['login_fail'] = '用户名密码不匹配！'
    return render(request, 'web_analysis/login.html', context=context)


# 注销
def my_logout(request):
    logout(request)
    return redirect('login')


# 注册
def signup(request):
    context = {}
    if request.method == 'POST':
        username = str(request.POST['usernameInput'])
        p1 = str(request.POST['passwordInput1']).strip()
        p2 = str(request.POST['passwordInput2']).strip()
        if username and p1 == p2:
            try:
                user = User.objects.create_user(username, '', p1)
                login(request, user)
                return redirect('home')
            except IntegrityError:
                context['register_fail'] = 'fail'
        else:
            context['register_fail'] = 'fail'
    return render(request, 'web_analysis/signup.html', context=context)


# 主页
@login_required(login_url='/web/login')
def home(request):
    user = request.user
    return render(request, 'web_analysis/base.html', context={'user': user.username})


# 搜索量分析
@login_required(login_url='/web/login')
def quantity(request):
    user = request.user
    if request.method == 'POST':
        limit = str(request.POST['topn'])
        if limit and limit.isdigit():
            results_title = '排名前 ' + limit + ' 的用户情况'
            results = db_util.select_top_search_volume(int(limit))
        else:
            results_title = '输入数字有误：' + limit + '。默认排名前 20 的用户情况'
            results = db_util.select_top_search_volume(20)
    else:
        results_title = '默认排名前 20 的用户情况'
        results = db_util.select_top_search_volume(20)
    # 构建绘建图标的数据
    user_labels = [r['initialid'] for r in results]
    user_values = [r['count'] for r in results]
    context = {'results': results, 'results_title': results_title, 'user': user.username, 'user_values': user_values, 'user_labels': user_labels}
    return render(request, 'web_analysis/quantity.html', context=context)


# https://sm.ms/ 图床
def upload_img(img_src: str):
    headers = {
        'Authorization': '1pfLgbOmsKxwLMsaOPs4X0uyHRO5W63V'
    }
    files = {
        'smfile': open(img_src, 'rb')
    }
    url = 'https://sm.ms/api/v2/upload'
    res = requests.post(url, files=files, headers=headers).json()
    return res


# 搜索关键词分析，词云
@login_required(login_url='/web/login')
def word_cloud(request):
    user = request.user
    context = {'user': user.username}
    if request.method == 'POST':
        uiid = str(request.POST['uiid']).strip()
        if uiid:
            context['uiid'] = uiid
            results = db_util.select_search_query(uiid)
            if len(results) > 0:
                words = []
                for r in results:
                    words.extend(jieba.lcut(r))
                words_counter = Counter(words)
                wc_data = [{'name': x, 'value': y} for x, y in words_counter.items()]
                context['wc_data'] = wc_data
                # 关键词计数
                wc = []
                counter = Counter(results)
                for x, y in counter.items():
                    wc.append({'word': x, 'count': y})
                wc.sort(key=lambda e: e['count'], reverse=True)
                context['wordcount'] = wc
            else:
                context['error_message'] = '未查找到用户的相关记录，请检查输入的用户原始 ID！'
        else:
            context['error_message'] = '未查找到用户的相关记录，请检查输入的用户原始 ID！'
    return render(request, 'web_analysis/wordcloud.html', context=context)


# 上网时间分析
@login_required(login_url='/web/login')
def user_time(request):
    user = request.user
    context = {'user': user.username}
    if request.method == 'POST':
        uiid = str(request.POST['uiid']).strip()
        if uiid:
            context['uiid'] = uiid
            results = db_util.select_user_time(uiid)
            if len(results) > 0:
                minutes_counter = Counter(results)
                m_data = [minutes_counter[x] if minutes_counter[x] is not None else 0 for x in range(24)]
                context['time_data'] = m_data
                print(m_data)
            else:
                context['error_message'] = '未查找到用户的相关记录，请检查输入的用户原始 ID！'
        else:
            context['error_message'] = '未查找到用户的相关记录，请检查输入的用户原始 ID！'
    return render(request, 'web_analysis/usertime.html', context=context)


# 点击 URL 分析
@login_required(login_url='/web/login')
def user_url(request):
    user = request.user
    context = {'user': user.username}
    if request.method == 'POST':
        uiid = str(request.POST['uiid']).strip()
        if uiid:
            context['uiid'] = uiid
            results = db_util.select_user_url(uiid)
            if len(results) > 0:
                context['url_data'] = results
                context['url_data_label'] = [r['name'] for r in results]
                print(results)
            else:
                context['error_message'] = '未查找到用户的相关记录，请检查输入的用户原始 ID！'
        else:
            context['error_message'] = '未查找到用户的相关记录，请检查输入的用户原始 ID！'
    return render(request, 'web_analysis/userurl.html', context=context)


@login_required(login_url='/web/login')
def keyword(request):
    user = request.user
    context = {'user': user.username}
    if request.method == 'POST':
        kw = str(request.POST['keywordInput']).strip()
        if kw:
            context['kw'] = kw
            results = db_util.select_keyword(kw)
            if len(results) > 0:
                context['results'] = results
                context['results_title'] = '关键词：“' + kw + '”被检索次数'
                context['user_labels'] = [r['uiid'] for r in results[:20]]
                context['user_values'] = [r['count'] for r in results[:20]]
            else:
                context['error_message'] = '未查找到该关键词的相关记录，请重新输入！'
        else:
            context['error_message'] = '输入的关键词不合法，请重新输入！'
    return render(request, 'web_analysis/keyword.html', context=context)
