from django.shortcuts import render

from snownlp import SnowNLP
from paddlemodel.network import *


MODEL_PATH = BASE_DIR_STRING + '/model'
model = Network()

# Create your views here.
def index(request):
    context = {}
    if request.method == 'POST':
        news = request.POST['newsInput']
        context['raw_input'] = news
        if news:
            snow = SnowNLP(news)
            summary = snow.summary(3)
            _summay_all = ' '.join(summary)
            context['summary'] = summary
            result = predict(model, MODEL_PATH, _summay_all)
            context['result'] = result
        else:
            context['error'] = '输入错误，请重新输入！'
    return render(request, 'news_classification/index.html', context=context)