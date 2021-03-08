from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('detail/<int:id>', views.detail, name='detail'),
    path('generate', views.generate, name='generate')
]