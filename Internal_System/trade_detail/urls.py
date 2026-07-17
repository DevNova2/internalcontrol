#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/10 17:16
# @Author  : Neo
# @File    : urls.py
# @Software: PyCharm
# 说明:


from django.urls import path

from . import views

app_name = 'trade_detail'

urlpatterns = [
    path('detail/<str:the_date>', views.trade_detail, name='trade_detail'),
    path('pro_trade_detail/', views.index_stra_detail, name='pro_trade_detail'),
    path('internal_control/', views.internal_control_page, name='internal_control'),
    path('api/internal-control/', views.internal_control_api, name='internal_control_api'),
]
