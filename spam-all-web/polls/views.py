import os
import shutil

import re
from django.shortcuts import render

from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.views.decorators.csrf import requires_csrf_token

from SpamWeb.settings import BASE_DIR
from spam.bayes import BayesSpam
from spam.dt_main import DTMain
from spam.preprocess_data import *
from spam.svm_sci import SVMSCI

bs_global = BayesSpam(train_file_list=None, test_file_list=None, spam_set=None, user_data=True, flag=True)
svm_global = SVMSCI()
dt_global = DTMain()


def index(request):
  if request.method == 'GET':
    print(request.GET)
    if len(request.GET.dict().keys()) == 0:
      return render(request, 'index.html')
    method = int(request.GET.get('algoSelect', default='0'))
    if method == 1:
      acc, precision, recall, f1 = bs_global.web_train()
      return render(request, 'index.html', context={'acc': f"{acc:.4f}", 'algo': '朴素贝叶斯',
                                                    'precision': f"{precision:.4f}", 'recall': f"{recall:.4f}", 'f1': f"{f1:.4f}"})
    elif method == 2:
      acc, precision, recall, f1 = svm_global.train()
      return render(request, 'index.html', context={'acc': f"{acc:.4f}", 'algo': 'SVM', 'precision': f"{precision:.4f}", 'recall': f"{recall:.4f}",
                                                    'f1': f"{f1:.4f}"})
    elif method == 3:
      acc, precision, recall, f1 = dt_global.train()
      return render(request, 'index.html',
                    context={'acc': f"{acc:.4f}", 'algo': '决策树', 'precision': f"{precision:.4f}", 'recall': f"{recall:.4f}",
                             'f1': f"{f1:.4f}"})
    else:
      return render(request, 'index.html',
                    context={'invalid': '无效的模型！'})

  return render(request, 'index.html')


def makeResultDict(r: bool) -> dict:
  result = {}
  if r:
    result['label'] = '垃圾邮件'
    result['value'] = 'spam'
    result['style'] = 'badge badge-danger'
  else:
    result['label'] = '正常邮件'
    result['value'] = 'ham'
    result['style'] = 'badge badge-success'
  return result


def analysis(request):
  if request.method == 'POST':
    print(request.POST)
    content = request.POST.get('emailtext')
    if content:
      bs_global.load_model(BASE_DIR + '/model')
      result_svm = makeResultDict(svm_global.svm_test_one(content))
      result_bs = makeResultDict(bs_global.test_single_email(content))
      result_dt = makeResultDict(dt_global.test_one(content))
      last_email_text = content
      return render(request, 'analysis.html', context={'result_svm': result_svm, 'result_bs': result_bs, 'result_dt': result_dt, 'last_email_text': last_email_text})
  return render(request, 'analysis.html')
