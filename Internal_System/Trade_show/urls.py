# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: urls.py
@time: 2023/5/25 9:57
说明:
"""
from django.urls import path
from . import views

app_name = 'Trade_show'

urlpatterns = [
    path('dash_app/', views.dash_app_view, name='dash_app'),  # 添加此行
]
