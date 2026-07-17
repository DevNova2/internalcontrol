#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 12:27
# @Author  : Neo.Zhu
# @File    : views.py
# @Power By: PyCharm
# 说明:
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
'''
这段代码定义了一个名为home_page的视图函数，
用于展示网站的主页。主页要求用户必须先登录才能访问，
因此使用了@login_required装饰器进行限制。如果用户未登录，将会被重定向到登录页面。
'''

@login_required(login_url='/admin/login/?next=/')
def home_page(request):
    return redirect('/quo/latest')
