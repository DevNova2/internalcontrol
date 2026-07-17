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

app_name = 'trade_loss'

urlpatterns = [
    path('loss_detail/<str:pro>', views.loss_index, name='loss_detail'),
    path('loss_cmp/', views.loss_the_date, name='loss_cmp'),

]
