#-*- coding: utf-8 -*-

""" APP NAME: Python Weibo OAuth2 Template """
""" Author  : xiaomo(wxm4ever@gmail.com)   """
""" Fork    : https://github.com/wangxiaomo/py-weibo-oauth2template/fork_select """

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from datetime import datetime


""" Read Config From Config.yaml """
import yaml
with open('config.yaml') as f:
    config = yaml.load(f)

APP_KEY = config['APP_KEY']
APP_SECRET = config['APP_SECRET']
CALLBACK_URL = config['CALLBACK_URL']
DEBUG = config['DEBUG']
SECRET_KEY = config['SECRET_KEY']

from flask import Flask, g, request, redirect, make_response, flash, render_template, session, jsonify
app = Flask(__name__)
app.config.from_object(__name__)

try:
    import json
except ImportError:
    import simplejson as json
from weibo import APIClient
from DB import MySQL


def get_api_client():
    """ 返回 API Client """
    return APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)

@app.route("/")
def index():
    client = get_api_client()
    try:
        if request.cookies['is_login'] != 'True' or session['is_login'] != 1:
            raise Exception("Haven't Login")
    except:
        auth_url = client.get_authorize_url()
        return redirect(auth_url)
    else:
        #TODO:不确定新浪OAuth2的access_key多会过期．
        ret = []
        status = list(show_status())
        for s in status:
            tmp = [] 
            tmp.extend(s)
            status_id = s[0]
            comments = get_status_comments(status_id)
            tmp.append(comments)
            ret.append(tmp)
        return render_template('index.html', status=ret)

@app.route("/callback")
def callback():
    try:
        code   = request.args.get("code")
        client = get_api_client()
        r = client.request_access_token(code)
        client.set_access_token(r.access_token, r.expires_in)
        userid=client.get.account__get_uid()
        user=client.get.users__show(uid=userid.uid)
        
        # 更新 users 表
        update_user_info(userid["uid"], user["name"], r.access_token, r.expires_in)
        # 写回 cookie && Session
        session['is_login'] = 1
        session['uid'] = userid["uid"]
        session['screen_name'] = user["name"]

        resp = app.make_response(redirect('/'))
        resp.set_cookie('is_login', 'True')
        resp.set_cookie('uid', userid["uid"])
        resp.set_cookie('screen_name', user["name"])
        return resp
    except Exception as e:
        return "*** OAuth2 Failed: %s" % str(e)

@app.route("/post", methods=['GET','POST'])
def post():
    """ 发布秘密 """
    err = 0
    params = request.values

    # 添加秘密
    status = params.get('status')
    uid = session['uid']
    ret = add_status(uid, status)
    if ret == True:
        msg = "添加成功!"
    else:
        err = 1
        msg = "*** Exception: %s" % ret 
    return jsonify(err=err,msg=msg)

@app.route("/status/<int:status_id>", methods=['GET', 'POST'])
def post_comment(status_id):
    """ 发布评论 """
    err = 0
    params = request.values

    # 添加评论
    comment = params.get('comment')
    uid = session['uid']
    ret = add_comment(status_id, uid, comment)
    if ret == True:
        msg = "评论成功!"
    else:
        err = 1
        msg = "*** Exception: %s" % ret 
    return jsonify(err=err,msg=msg)

@app.route("/logout")
def logout():
    session['is_login'] = 0
    session['uid'] = ''
    session['screen_name'] = ''
    resp = app.make_response(redirect('/'))
    resp.set_cookie('is_login', 'False')
    resp.set_cookie('uid', '')
    resp.set_cookie('screen_name', '')
    return resp

@app.route("/test")
def test():
    ret = test_db()
    return "插入成功!"+ret[0][1]

#----------------------------------------------------------
# Helper Functions
#----------------------------------------------------------
def update_user_info(uid, screen_name, access_key, expires):
    try:
        db = MySQL()
        sql = "SELECT uid FROM users WHERE uid=%d" % uid
        ret = db.query(sql)
        if not ret:
            # 新增用户
            sql = "INSERT INTO users(uid,screen_name,access_key,expires) VALUES(%d,'%s','%s',%d)" \
                % (uid, quote_sql(screen_name), str(access_key), expires)
        else:
            # 更新用户
            sql = "UPDATE users SET screen_name='%s',access_key='%s',expires=%s WHERE uid=%d"     \
                % (quote_sql(screen_name), access_key, expires, uid)
        db.update(sql)
        return True
    except Exception as e:
        return str(e)

def show_status(page=0, count=20):
    try:
        db = MySQL()
        sql = "SELECT * FROM status ORDER BY pub_time DESC LIMIT %d,%d" % (page*count, count)
        ret = db.query(sql)
        return ret
    except Exception as e:
        return str(e)

def add_status(uid, status):
    try:
        db = MySQL()
        time = get_time(datetime.now())
        sql = "INSERT INTO status(status,uid,pub_time) VALUES('%s', %d, '%s')" \
                % (quote_sql(status), int(uid), time)
        db.update(sql)
        return True
    except Exception as e:
        return str(e)

def add_comment(status_id, uid, comment):
    try:
        db = MySQL()
        time = get_time(datetime.now())
        sql = "INSERT INTO comments(post_id, uid, comment, pub_time) VALUES(%d, %d, '%s', '%s')" \
                % (status_id, uid, quote_sql(comment), time)
        db.update(sql)
        return True
    except Exception as e:
        return str(e)

def get_status_comments(status_id):
    try:
        db = MySQL()
        sql = "SELECT * FROM comments WHERE post_id=%d ORDER BY pub_time" % status_id
        ret = db.query(sql)
        return ret 
    except Exception as e:
        return str(e)

def quote_sql(msg):
    return msg.replace("\\", "\\\\").replace("'","''")

def get_time(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")

def test_db():
    db = MySQL()
    sql = "SELECT * FROM users"
    ret = db.query(sql)
    return ret
