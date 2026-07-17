#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/23 14:49
# @Author  : Neo.Zhu
# @File    : urls.py
# @Power By: PyCharm
# 说明:
from django.urls import path

from . import views

app_name = 'quo'

urlpatterns = [
    path('<str:the_date>', views.chg_dist, name='chg_dist'),

]
