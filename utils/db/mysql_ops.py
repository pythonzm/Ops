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
import re
import pymysql
import logging
from pymysql.err import OperationalError, ProgrammingError
from pymysql.connections import Connection

GLOBAL_PRIVIS = {'CREATE TABLESPACE', 'CREATE USER', 'FILE', 'PROCESS', 'REPLICATION CLIENT', 'REPLICATION SLAVE',
                 'SHOW DATABASES', 'SHUTDOWN', 'SUPER', 'RELOAD'}


class MysqlPool:

    def __init__(self, host, port, user, password, db, max_pool_size=50, charset='utf8', timeout=5):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.max_pool_size = max_pool_size
        self.charset = charset
        self.timeout = timeout
        self.pool = None
        self.cursorclass = pymysql.cursors.DictCursor
        self._initialize_pool()

    def _initialize_pool(self):
        self.pool = Queue(maxsize=self.max_pool_size)
        for i in range(self.max_pool_size):
            conn = Connection(host=self.host, port=self.port, user=self.user, password=self.password, db=self.db,
                              charset=self.charset, connect_timeout=self.timeout)
            self.pool.put_nowait(conn)

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

    def exec_select(self, sql, args=None, size=None, one=False):
        """
        执行有返回结果集的sql,主要是select
        """
        conn = None
        try:
            conn = self.pool.get()
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                table_heads = [des[0] for des in cursor.description]
                if one:
                    result = cursor.fetchone()
                    return table_heads, result
                if size:
                    results = cursor.fetchmany(size)
                    return table_heads, results
                else:
                    results = cursor.fetchall()
                    return table_heads, results
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
            raise e
        finally:
            conn.close()
            self.pool.put_nowait(conn)

    def get_tables(self, sql='show tables'):
        """
        获取当前数据库所有的表
        """
        _, tables = self.exec_select(sql)
        names = [t[0] for t in tables]
        return names

    def get_dbs(self, sql='show databases'):
        """
        获取当前数据库所有的数据库
        """
        _, dbs = self.exec_select(sql)
        names = [d[0] for d in dbs if d[0] not in ('information_schema', 'performance_schema', 'mysql')]
        return names

    def get_all_users(self):
        users = self.exec_select("SELECT user,host FROM user")
        return (user for user in users[1] if user[0] not in ['', 'root', ])

    def close_conn(self):
        for i in range(self.max_pool_size):
            self.pool.get().close()

    def server_version_check(self):
        _, result = self.exec_select("SELECT VERSION()", one=True)
        version_str = result[0]
        version = version_str.split('.')

        if 'mariadb' in version_str.lower():
            return True
        if int(version[0]) <= 5 and int(version[1]) < 7:
            return True
        else:
            return False

    def user_exists(self, user, host):
        _, count = self.exec_select("SELECT count(*) FROM user WHERE user = %s AND host = %s", (user, host), one=True)
        return count[0] > 0

    def user_add(self, user, host, password, db_table=None, privs=None):
        """
        :param user:
        :param host:
        :param password:
        :param db_table: 格式：db_name.table_name
        :param privs:
        :type privs: list, tuple
        :return:
        """
        if self.user_exists(user, host):
            raise UserExistError("用户已存在！")
        self.exec_sql_one("CREATE USER %s@%s IDENTIFIED BY %s", (user, host, password))
        if db_table and privs:
            self.privileges_grant(user, host, db_table, privs)

    def user_delete(self, user, host):
        self.exec_sql_one("DROP USER %s@%s", (user, host))

    def user_mod(self, user, host, password=None, new_user=None, new_host=None):
        # 修改密码
        if password:
            old_user_mgmt = self.server_version_check()
            if old_user_mgmt:
                self.exec_sql_one("SET PASSWORD FOR %s@%s = PASSWORD(%s)", (user, host, password))
            else:
                self.exec_sql_one("ALTER USER %s@%s IDENTIFIED WITH mysql_native_password BY %s",
                                  (user, host, password))
            return

        # 修改用户名或主机
        u = new_user if new_user else user
        h = new_host if new_host else host

        self.exec_sql_one("RENAME USER %s@%s TO %s@%s", (user, host, u, h))
        return

    def privileges_get(self, user: str, host: str) -> dict:
        """ MySQL doesn't have a better method of getting privileges aside from the
        SHOW GRANTS query syntax, which requires us to then parse the returned string.
        Here's an example of the string that is returned from MySQL:

         GRANT USAGE ON *.* TO 'user'@'localhost' IDENTIFIED BY 'pass';

        This function makes the query and returns a dictionary containing the results.
        The dictionary format is the same as that returned by privileges_unpack() below.
        """
        output = {}
        _, grants = self.exec_select("SHOW GRANTS FOR %s@%s", (user, host))
        for grant in grants:
            res = re.match("GRANT (.+) ON (.+) TO '.*'@'.*'( IDENTIFIED BY PASSWORD '.+')? ?(.*)", grant[0])
            if res.group(1) == 'USAGE':
                continue
            privileges = res.group(1).split(", ")
            if "WITH GRANT OPTION" in res.group(4):
                privileges.append('GRANT')
            if "REQUIRE SSL" in res.group(4):
                privileges.append('REQUIRESSL')
            db = res.group(2)
            output[db] = privileges
        return output

    def privileges_grant(self, user, host, db_table, privs):
        """
        :param user:
        :param host:
        :param db_table: 格式：db_name.table_name
        :param privs:
        :type privs: tuple, list
        :return:
        """
        if not set(privs).isdisjoint(GLOBAL_PRIVIS) and db_table != '*.*':
            raise GlobalPrivilegeError("全局权限不能对单个库授权，需要指定*.*")
        db_table = db_table.replace('%', '%%')
        priv_string = ",".join([p for p in privs if p not in ('GRANT', 'REQUIRESSL')])
        query = ["GRANT %s ON %s" % (priv_string, db_table), "TO %s@%s"]
        if 'GRANT' in privs:
            query.append("WITH GRANT OPTION")
        query = ' '.join(query)
        self.exec_sql_one(query, (user, host))

    def privileges_revoke(self, user, host, db_table, privs, grant_option=False):
        """
        :param user:
        :param host:
        :param db_table: 格式：db_name.table_name
        :param privs:
        :type privs: list, tuple
        :param grant_option:
        :return:
        """
        if not set(privs).isdisjoint(GLOBAL_PRIVIS) and db_table != '*.*':
            raise GlobalPrivilegeError("全局权限不能对单个库撤销权限，需要指定*.*")
        db_table = db_table.replace('%', '%%')
        if grant_option:
            query = ["REVOKE GRANT OPTION ON %s" % db_table, "FROM %s@%s"]
            query = ' '.join(query)
            self.exec_sql_one(query, (user, host))
        priv_string = ",".join([p for p in privs if p not in ('GRANT', 'REQUIRESSL')])
        query = ["REVOKE %s ON %s" % (priv_string, db_table), "FROM %s@%s"]
        query = ' '.join(query)
        self.exec_sql_one(query, (user, host))

    def user_all(self) -> list:
        output = []
        users = self.get_all_users()
        for user in users:
            try:
                grants = self.privileges_get(user[0], user[1])
                output.append({'user': f'{user[0]}@{user[1]}', 'privs': grants})
            except TypeError:
                output.append({'user': f'{user[0]}@{user[1]}', 'privs': ''})
        return output


class UserExistError(Exception):
    pass


class GlobalPrivilegeError(Exception):
    pass


if __name__ == '__main__':
    m = MysqlPool('10.1.7.198', 3306, 'cc', '123456', 'mysql')

    a = m.user_all()
    print(a)
    # m.user_mod('hello1', '10.%.%.%', new_user='world', new_host='%')
    # _, r = m.exec_select("SELECT VERSION()", one=True)
    # print(r[0])
    # m.user_delete('iamdcdb', '%')
    # m.user_add('hello', '%', '123456', 'blog.*', ['select'])
    # m.privileges_grant('bb', '%', 'devops.*', ['RELOAD'])
    # o = m.privileges_get('jrops', '%')
    # print(o)
    # m.privileges_revoke('cmdb', '10.1.7.%', 'devops.*', ("update", "delete"))
    # r = m.exec_select(r'select User,Host from user')
    # print(r[1])
    # users = ('@'.join(map(lambda x: json.dumps(x), i)) for i in r[1] if i[0] not in ['root', ''])
    # for i in users:
    #     a = m.exec_select(f'show grants for {i}')
    #     print(i)
    #     if len(a[1]) > 1:
    #         print(a[1][1:])
    #     else:
    #         print(a[1][0])
