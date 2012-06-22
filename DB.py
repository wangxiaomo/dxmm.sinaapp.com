#-*- coding: utf-8 -*-

""" SAE MySQL Parser            """
""" xiaomo(wxm4ever@gmail.com)  """

import sae.const
HOST = sae.const.MYSQL_HOST
PORT = sae.const.MYSQL_PORT
DB   = sae.const.MYSQL_DB
USER = sae.const.MYSQL_USER
PASS = sae.const.MYSQL_PASS

import MySQLdb

class MySQL(object):
    """ SAE MySQL Parser """
    def __init__(self):
        self.conn = MySQLdb.connect(host=HOST,port=int(PORT),db=DB,user=USER,passwd=PASS,charset='utf8')
        self.cursor = self.conn.cursor()

    def query(self, sql):
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except:
            raise

    def update(self, sql):
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            return True
        except:
            raise

    def __del__(self):
        self.cursor.close()
        self.conn.close()
