#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 14:46
# @Author  : Neo
# @File    : urls.py
# @Software: PyCharm
# 说明:


from django.urls import path

from . import views

app_name = 'paper_trade'

urlpatterns = [
    path('index/<str:pro>/<str:double_turn_loss>', views.pro_index, name='index'),
    path('snd/<str:pro>/<str:double_turn_loss>', views.pro_snd, name='snd'),
]
