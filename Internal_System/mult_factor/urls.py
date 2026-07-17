# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: urls.py
@time: 2023/5/22 11:21
说明:
"""
from django.urls import path

from . import views

app_name = 'stra'

urlpatterns = [
    path('style_factor/<str:begin_date>', views.style_factor, name='style_factor'),
    path('cap_dist/<str:the_date>', views.mkt_cap_hist, name='mkt_cap_hist'),
    path('ic_ir/<str:the_date>', views.ic_ir, name='ic_ir'),
    path('weight/<str:the_date>', views.weight, name='weight'),
    path('monotonic/<str:factor>/<str:begin_date>', views.monotonic, name='monotonic'),
]
