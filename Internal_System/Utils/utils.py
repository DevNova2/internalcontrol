# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: utils.py
@time: 2023-07-27 10:20
说明:
"""
import datetime
import subprocess
import time
import os
import sys
import ctypes
import pandas as pd
from inspect import currentframe, stack, getmodule
from decimal import Decimal
from Utils.my_errors import ParamsError


def get_screen_size():
    user32 = ctypes.windll.user32
    screen_size0 = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return screen_size0


def get_root_path():
    # 获取根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 修改成linux目录
    base_dir = base_dir.replace('\\', '/')
    return base_dir


def get_log_path():
    log_dir = '/logs/'
    return get_root_path() + log_dir


def is_list(l):
    return isinstance(l, (list, tuple))


def convert_fields_to_str(s):
    if isinstance(s, (list, tuple)):
        res = [str(item) for item in s]
        return res
    else:
        raise ParamsError("参数应该是 list or tuple")


def get_mac_address():
    import uuid
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    return '%s:%s:%s:%s:%s:%s' % (mac[0:2], mac[2:4], mac[4:6], mac[6:8], mac[8:10], mac[10:])


def get_security_type(security):
    exchange = security[-4:]
    code = security[:-5]
    if code.isdigit():
        if exchange == "XSHG":
            if code >= "600000" or code[0] == "9":
                return "stock"
            elif code >= "500000":
                return "fund"
            elif code[0] == "0":
                return "index"
            elif len(code) == 8 and code[0] == '1':
                return "option"
        elif exchange == "XSHE":
            if code[0] == "0" or code[0] == "2" or code[:3] == "300":
                return "stock"
            elif code[:3] == "399":
                return "index"
            elif code[0] == "1":
                return "fund"
        else:
            raise Exception("找不到标的%s" % security)
    else:
        if exchange in ("XSGE", "XDCE", "XZCE", "XINE", "CCFX"):
            if len(code) > 6:
                return "option"
            return "future"
    return 0


def isatty(stream=None):
    stream = stream or sys.stdout
    _isatty = getattr(stream, 'isatty', None)
    return _isatty and _isatty()


def get_cur_info():
    f_current_line = str(currentframe().f_back.f_lineno)  # 哪一行调用的此函数
    mod = getmodule(stack()[1][0])  # 调用函数的信息
    f = mod.__file__
    module_name = mod.__name__  # 函数名
    return {'文件': f.replace('\\', '/'), '模块': module_name, '行号': f_current_line}


def trans_str_to_decimal(df: pd.DataFrame, exp_cols=None, trans_cols=None) -> pd.DataFrame:
    """
    对df中指定 trans_cols 各个列(除了exp_cols中)转换为 Decimal
    如果exp_cols，trans_cols同时指定，最终返回的以 exp_cols 指定的为准
    :param trans_cols:
    :param df_src:
    :param exp_cols:
    :return:
    """
    if (trans_cols is None) and (exp_cols is None):
        raise Exception("类型转换时，排除列列表和指定转换列列表不能同时为空，至少指定一个")
    if exp_cols is not None:
        trans_cols = list(set(df.columns) - set(exp_cols))
    for v in df.columns.values:
        if v in trans_cols:
            df[v] = df[v].apply(Decimal)
    return df


def trans_str_to_float64(df: pd.DataFrame, exp_cols: list = None, trans_cols: list = None) -> pd.DataFrame:
    """如果给定 exp_cols 就不会考虑 trans_cols ，如果都不指定，就全部转"""
    if (trans_cols is None) and (exp_cols is None):
        trans_cols = df.columns
    if not (exp_cols is None):
        trans_cols = list(set(df.columns) - set(exp_cols))
    df[trans_cols] = df[trans_cols].astype('float64')
    return df


def my_decimal_format(df, cols):
    df = df.copy()
    for col in cols:
        df[col] = df[col].apply(lambda x: format(x, '.10%'))
    return df


def throw_exception(name):
    print('子进程%s发生异常,进程号为%s' % (name, os.getpid()))
    cmd = 'taskkill /im ' + str(os.getpid()) + ' /F'
    res = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    print(res.stdout.read())
    print(res.stderr.read())
    time.sleep(2)


def get_week_month_date(the_date=None, week=False, month=False):
    """获取本周（本月）的第一天和最后一天"""
    if the_date is None:
        today = datetime.datetime.today().date()
    else:
        today = datetime.datetime.fromisoformat(the_date)
    if week:
        this_week_start = today - datetime.timedelta(days=today.weekday())
        this_week_end = today + datetime.timedelta(days=6 - today.weekday())
        return str(this_week_start.date()), str(this_week_end.date())
    elif month:
        t_m = today.month + 1 if today.month < 12 else 1

        this_month_start = datetime.datetime(today.year, today.month, 1)
        this_month_end = datetime.datetime(today.year, t_m, 1) - datetime.timedelta(
            days=1) + datetime.timedelta(
            hours=23, minutes=59, seconds=59)
        return str(this_month_start.date()), str(this_month_end.date())
    return str(today), str(today)


def stamp2time(timeStamp, fmt='T'):
    """
    功能：将时间戳转换成日期函数 例如：1606708276268 ==》2020-11-30 11:51:16
    参数：timeStamp 时间戳，类型 double 例如：1606708276268
    返回值：日期， 类型：字符串 2020-11-30 11:51:16
    """
    time_local = time.localtime(timeStamp / 1000)
    if fmt == 'T':
        dt = time.strftime("%Y-%m-%d", time_local)
    elif fmt == 'D':
        dt = time.strftime("%H:%M:%S", time_local)
    else:
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt
