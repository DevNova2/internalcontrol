# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: urls.py
@time: 2023/5/23 12:38
说明:
"""
from django.urls import path

from . import views

app_name = 'dq_alpha_one'

urlpatterns = [
    path('', views.home_page, name='home_page'),
    # path('alpha_one_index/', views.dq_alpha_one, name='alpha_one_index'),

    # path('<int:pk>/', views.PhoneNumDetailView.as_view(), name='detail'),
    #
    # path('recover/', views.recover, name='recover'),
    # path('recover/<str:req>/', views.recover, name='recover'),

    # path('dashboard/', views.dashboard, name='dashboard'),

    #     path('search/', views.search, name='search'),
    #
    #     path('<int:pk>/export/', views.export_data, name="export"),
    #     path('import_sheet/', views.import_sheet, name="import_sheet"),
]
