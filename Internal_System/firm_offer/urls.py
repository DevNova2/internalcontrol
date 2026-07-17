#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/5 17:16
# @Author  : Neo
# @File    : urls.py
# @Software: PyCharm
# 说明:
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'firm_offer'

urlpatterns = [
    # path('', views.home_page, name='home_page'),
    path('index/<str:pro_id>', views.firm_index, name='index'),
    path('pdf', views.pdf_detail, name='luyan_pdf'),
    path('login/', auth_views.LoginView.as_view(template_name='firm_offer/login.html', next_page='/'), name='user_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='user_logout'),

    # path('<int:pk>/', views.PhoneNumDetailView.as_view(), name='detail'),
    #
    #
    # path('recover/<str:req>/', views.recover, name='recover'),

    # path('dashboard/', views.dashboard, name='dashboard'),

    #     path('search/', views.search, name='search'),
    #
    #     path('<int:pk>/export/', views.export_data, name="export"),
    #     path('import_sheet/', views.import_sheet, name="import_sheet"),
]
