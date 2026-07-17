# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: db_client.py
@time: 2023-09-10 13:35
说明: 对再用数据库服务器精选剥离，并对基础库服务器做权限控制
"""
import pymongo
from urllib.parse import quote_plus

#连接mongodb数据库
def get_client(c_from='local'):
    client_dict = {
        'local': '127.0.0.1:27017',
        'neo': '192.168.1.77:27017/',
        'dev': '192.168.1.78:27017/',
        'strategy': '192.168.1.76:27017/',
        'db_u': 'Tom:tom@192.168.1.99:29900/',
    }
    client_name = client_dict.get(c_from, None)
    if client_name is None:
        raise Exception(f'传入的数据库目标服务器有误 {client_name}，请检查 {client_dict}')
    return pymongo.MongoClient("mongodb://{}".format(client_name))


def get_client_U(m='r'):
    if m == 'r':
        user, pwd = 'Tom', 'tom'
    else:
        user, pwd = 'Tom', 'tom'
    return pymongo.MongoClient("mongodb://%s:%s@%s" % (quote_plus(user),
                                                       quote_plus(pwd),
                                                       '192.168.1.99:29900/'))
