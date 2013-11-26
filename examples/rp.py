#-*-coding:utf-8-*-

# 人人刷人品


import time
from datetime import datetime
from pyrenren import RenRen

renren = RenRen('email', 'password')

while True:
    print str(datetime.now()), 'refresh index'
    renren.get('http://www.renren.com')
    time.sleep(30 * 60)
