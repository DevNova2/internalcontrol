#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 11:33
# @Author  : Neo.Zhu
# @File    : middleware.py
# @Power By: PyCharm
"""
说明:

"""
from django.shortcuts import redirect
from django.conf import settings


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = settings.LOGIN_URL
        self.open_urls = [self.login_url] + getattr(settings, 'OPEN_URLS', [])
        self.open_url_prefixes = getattr(settings, 'OPEN_URL_PREFIXES', [])

    def __call__(self, request):
        request_path = request.path_info or '/'
        request_path_with_slash = request_path if request_path.endswith('/') else f'{request_path}/'
        is_open_path = request_path in self.open_urls or request_path_with_slash in self.open_urls or any(
            request_path.startswith(prefix) or request_path_with_slash.startswith(prefix)
            for prefix in self.open_url_prefixes
        )
        if not request.user.is_authenticated and not is_open_path:
            return redirect(self.login_url + '?next=' + request.path)

        return self.get_response(request)
