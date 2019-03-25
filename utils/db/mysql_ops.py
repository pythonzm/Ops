# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      mysql_ops
   Description:
   Author:          Administrator
   date：           2018-12-20
-------------------------------------------------
   Change Activity:
                    2018-12-20:
-------------------------------------------------
"""
from queue import Queue
import logging
import pymysql
from pymysql.err import OperationalError, ProgrammingError
from pymysql.connections import Connection


class MysqlPool:

    def __init__(self, host, port, user, password, db, max_pool_size=50, charset='utf8'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.max_pool_size = max_pool_size
        self.charset = charset
        self.pool = None
        self.cursorclass = pymysql.cursors.DictCursor
        self._initialize_pool()

    def _initialize_pool(self):
        self.pool = Queue(maxsize=self.max_pool_size)
        for i in range(self.max_pool_size):
            try:
                conn = Connection(host=self.host, port=self.port, user=self.user, password=self.password, db=self.db,
                                  charset=self.charset)
                self.pool.put_nowait(conn)
            except Exception as e:
                logging.getLogger().error('初始化mysql连接池失败：{}'.format(e))
                break

    def exec_sql_one(self, sql, args=None):
        """
        执行无返回结果集的sql，主要有insert update delete
        """
        conn = None
        try:
            conn = self.pool.get()
            with conn.cursor(cursor=self.cursorclass) as cursor:
                res = cursor.execute(sql, args)
                conn.commit()
                return res
        except OperationalError:
            return '您无权执行该命令！'
        except ProgrammingError as e:
            return e
        except Exception as e:
            logging.getLogger().error('执行exec_sql失败：{}'.format(e))
            conn.rollback()
        finally:
            conn.close()
            self.pool.put_nowait(conn)

    def exec_select(self, sql, args=None):
        """
        执行有返回结果集的sql,主要是select
        """
        conn = None
        try:
            conn = self.pool.get()
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                res = cursor.fetchall()
                table_heads = [des[0] for des in cursor.description]
                return table_heads, res
        except ProgrammingError as e:
            return 'sql执行失败', str(e)
        except Exception as e:
            logging.getLogger().error('执行select语句失败：{}'.format(e))
        finally:
            conn.close()
            self.pool.put_nowait(conn)

    def exec_sql_many(self, sql, args=None):
        """
        执行多个sql，主要是insert into 多条数据的时候
        """
        conn = None
        try:
            conn = self.pool.get()
            with conn.cursor(cursor=self.cursorclass) as cursor:
                res = cursor.executemany(sql, args)
                conn.commit()
                return res
        except OperationalError:
            return '您无权执行该命令！'
        except ProgrammingError as e:
            return e
        except Exception as e:
            logging.getLogger().error('执行exec_sql_many失败：{}'.format(e))
            conn.rollback()
        finally:
            conn.close()
            self.pool.put_nowait(conn)

    def get_tables(self, sql='show tables'):
        """
        获取当前数据库所有的表
        """
        _, res = self.exec_select(sql)
        names = []
        for i in res:
            names.append(i[0])
        return names

    def close_conn(self):
        for i in range(self.max_pool_size):
            self.pool.get().close()
