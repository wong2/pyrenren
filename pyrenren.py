#-*-coding:utf-8-*-

"""
Copyright (c) 2013 wong2 <wonderfuly@gmail.com>
Copyright (c) 2013 hupili <hpl1989@gmail.com>

Original Author:
    Wong2 <wonderfuly@gmail.com>
Changes Statement:
    Changes made by Pili Hu <hpl1989@gmail.com> on
    Jan 10 2013:
        Support captcha.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import re
import os
import json
import time
import urllib
import random
import requests


# 人人的登录密码加密算法
def encrypt_string(e, m, s):

    def _encrypt_chunk(e, m, chunk):
        chunk = map(ord, chunk)

        # 补成偶数长度
        if not len(chunk) % 2 == 0:
            chunk.append(0)

        nums = [chunk[i] + (chunk[i + 1] << 8) for i in range(0, len(chunk), 2)]

        c = sum([n << i * 16 for i, n in enumerate(nums)])

        encrypted = pow(c, e, m)

        # 转成16进制并且去掉开头的0x
        return hex(encrypted)[2:]


    CHUNK_SIZE = 30  # 分段加密

    e, m = int(e, 16), int(m, 16)
    chunks = [s[:CHUNK_SIZE], s[CHUNK_SIZE:]] if len(s) > CHUNK_SIZE else [s]
    result = [_encrypt_chunk(e, m, chunk) for chunk in chunks]
    return ' '.join(result)[:-1]  # 去掉最后的'L'


# 人人各种接口
class RenRen(object):

    def __init__(self, email=None, pwd=None):
        self.session = requests.Session()
        self.token = {}

        if email and pwd:
            self.login(email, pwd)

    def login_by_cookie(self, cookie_str):
        cookie_dict = dict([v.split('=', 1) for v in cookie_str.strip().split(';')])
        self.session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        self.get_token()

    def login(self, email, pwd):
        key = self.get_encrypt_key()

        if self.get_show_captcha(email) == 1:
            fn = 'icode.%s.jpg' % os.getpid()
            self.get_icode(fn)
            print "Please input the code in file '%s':" % fn
            icode = raw_input().strip()
            os.remove(fn)
        else:
            icode = ''

        data = {
            'email': email,
            'origURL': 'http://www.renren.com/home',
            'icode': icode,
            'domain': 'renren.com',
            'key_id': 1,
            'captcha_type': 'web_login',
            'password': encrypt_string(key['e'], key['n'], pwd) if key['isEncrypt'] else pwd,
            'rkey': key.get('rkey', '')
        }
        url = 'http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=%f' % random.random()
        r = self.post(url, data)
        result = r.json()
        if result['code']:
            self.email = email
            r = self.get(result['homeUrl'])
            self.get_token(r.text)
        else:
            raise Exception('Login Error')

    def get_icode(self, fn):
        r = self.get("http://icode.renren.com/getcode.do?t=web_login&rnd=%s" % random.random())
        if r.status_code == 200 and r.raw.headers['content-type'] == 'image/jpeg':
            with open(fn, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            raise Exception('get icode failure')

    def get_show_captcha(self, email=None):
        r = self.post('http://www.renren.com/ajax/ShowCaptcha', data={'email': email})
        return r.json()

    def get_encrypt_key(self):
        r = requests.get('http://login.renren.com/ajax/getEncryptKey')
        return r.json()

    def get_token(self, html=''):
        p = re.compile("requestToken : '(.*)',\n_rtk : '(.*)'\n")

        if not html:
            r = self.get('http://www.renren.com')
            html = r.text

        result = p.search(html)
        self.token = {
            'requestToken': result.group(1),
            '_rtk': result.group(2)
        }

    def request(self, url, method, data={}):
        if data:
            data.update(self.token)

        if method == 'get':
            return self.session.get(url, data=data)
        elif method == 'post':
            return self.session.post(url, data=data)

    def get(self, url, data={}):
        return self.request(url, 'get', data)

    def post(self, url, data={}):
        return self.request(url, 'post', data)

    def get_user_info(self):
        r = self.get('http://notify.renren.com/wpi/getonlinecount.do')
        return r.json()

    def get_notifications(self):
        url = 'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&limit=50&begin=0&view=17'
        r = self.get(url)
        try:
            result = json.loads(r.text, strict=False)
        except Exception, e:
            result = []
        return result

    def remove_notification(self, notify_id):
        self.get('http://notify.renren.com/rmessage/remove?nl=' + str(notify_id))

    def get_doings(self, uid, page=0):
        url = 'http://status.renren.com/GetSomeomeDoingList.do?userId=%s&curpage=%d' % (str(uid), page)
        r = self.get(url)
        return r.json().get('doingArray', [])

    def get_doing_by_id(self, owner_id, doing_id):
        doings = self.get_doings(owner_id)
        doing = filter(lambda doing: doing['id'] == doing_id, doings)
        return doing[0] if doing else None

    def get_doing_comments(self, owner_id, doing_id):
        url = 'http://status.renren.com/feedcommentretrieve.do'
        r = self.post(url, {
            'doingId': doing_id,
            'source': doing_id,
            'owner': owner_id,
            't': 3
        })

        return r.json()['replyList']

    def get_comment_by_id(self, owner_id, doing_id, comment_id):
        comments = self.get_doing_comments(owner_id, doing_id)
        comment = filter(lambda comment: comment['id'] == int(comment_id), comments)
        return comment[0] if comment else None

    # 访问某人页面
    def visit(self, uid):
        self.get('http://www.renren.com/' + str(uid) + '/profile')

    def _get_chat_payload(self, data):
        payload_tmpl = u'''
          <message fname="{from_name}" from="{from_uid}@talk.m.renren.com" to="{to_uid}@talk.m.renren.com" type="chat">
            <richbody type="dialog" localid="{timestamp}">
              <font>{msg}</font>
            </richbody>
          </message>\n\u0000&{token}
        '''

        data.update({
            'token': urllib.urlencode(self.token),
            'timestamp': int(time.time()*1000),
        })

        payload = payload_tmpl.format(**data).encode('utf-8').strip()
        return payload

    def send_message(self, to_uid, msg):
        user_info = self.get_user_info()
        from_name = user_info['hostname']
        from_uid = user_info['hostid']

        payload = self._get_chat_payload({
            'from_name': from_name,
            'from_uid': from_uid,
            'to_uid': to_uid,
            'msg': msg
        })

        # init wpi cookie
        self.get('http://wpi.renren.com/comet_get', data={'mid': 0})
        r = self.session.post('http://wpi.renren.com/muc_chat', data=payload)
        return r.status_code == 200


if __name__ == '__main__':
    renren = RenRen('email', 'password')
