from django.urls import path

from . import views

app_name = 'news_classification'

urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('home', views.index, name='index'),
]