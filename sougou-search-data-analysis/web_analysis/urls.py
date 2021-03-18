from django.urls import path

from . import views

urlpatterns = [
    path('', views.my_login, name='login'),
    path('login', views.my_login, name='login'),
    path('signup', views.signup, name='signup'),
    path('logout', views.my_logout, name='logout'),
    path('home', views.home, name='home'),
    path('quantity', views.quantity, name='quantity'),
    path('wordcloud', views.word_cloud, name='wordcloud'),
    path('usertime', views.user_time, name='usertime'),
    path('userurl', views.user_url, name='userurl'),
    path('keyword', views.keyword, name='keyword'),
]