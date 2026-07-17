# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: views.py
@time: 2023/5/22 19:27
说明:
"""

from django.shortcuts import render


def home_page(request):
    context = {}
    return render(request, 'home_page.html', context)


