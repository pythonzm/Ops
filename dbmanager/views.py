import csv
import codecs
import logging
import datetime
from django.conf import settings
from utils.db.mysql_ops import MysqlPool
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from dbmanager.models import DBConfig, DBLog
from projs.models import Service
from assets.models import ServerAssets
from django.contrib.auth.models import Group
from utils.decorators import admin_auth
from utils.crypt_pwd import CryptPwd
from django.contrib.auth.decorators import permission_required

VALID_PRIVS = {'CREATE': '允许创建数据库和表', 'DROP': '允许删除数据库，表和视图', 'GRANT OPTION': '允许对账户赋权和取消权限',
               'LOCK TABLES': '允许对具有SELECT权限的表进行锁表操作', 'REFERENCES': '允许创建外键', 'EVENT': '允许使用事件调度器',
               'ALTER': '允许修改表', 'DELETE': '允许使用DELETE', 'INDEX': '允许创建和删除索引', 'INSERT': '允许使用INSERT',
               'SELECT': '允许使用SELECT', 'UPDATE': '允许使用UPDATE', 'CREATE TEMPORARY TABLES': '允许创建临时表',
               'TRIGGER': '允许触发器相关操作', 'CREATE VIEW': '允许创建和修改视图', 'SHOW VIEW': '允许使用 SHOW CREATE VIEW',
               'ALTER ROUTINE': '允许修改和删除存储过程', 'CREATE ROUTINE': '允许创建存储过程', 'EXECUTE': '允许执行存储过程',
               'FILE': '允许执行创建文件和读取文件相关操作', 'CREATE TABLESPACE': '允许创建、修改和删除表空间和日志文件组',
               'CREATE USER': '允许创建、删除、重命名用户和取消用户所有权限', 'PROCESS': '允许使用SHOW PROCESSLIST',
               'RELOAD': '允许使用FLUSH', 'REPLICATION CLIENT': '允许查看master和slave',
               'REPLICATION SLAVE': '允许读取从master复制过来的binlog文件', 'SHOW DATABASES': '允许使用SHOW DATABASES',
               'SHUTDOWN': '允许停止mysql服务', 'SUPER': '允许执行管理员命令，比如：CHANGE MASTER、KILL、PURGE BINARY LOGS、SET GLOBAL、debug',
               'ALL PRIVILEGES': '允许所有权限', 'USAGE': '没有任何权限，只允许登录'}


# 'PROXY': '允许用户代理(将用户权限代理给某个用户)

@admin_auth
def db_list(request):
    if request.method == 'GET':
        dbs = DBConfig.objects.select_related('db_server').all()

        services = Service.objects.select_related('project').select_related('service_asset').filter(
            service_name__icontains='mysql')
        groups = Group.objects.all()
        return render(request, 'dbmanager/db_list.html', locals())
    elif request.method == 'POST':
        try:
            db = DBConfig.objects.create(
                db_server=Service.objects.get(id=request.POST.get('db_server')),
                db_port=int(request.POST.get('db_port')),
                db_name=request.POST.get('db_name'),
                db_user=request.POST.get('db_user'),
                db_password=CryptPwd().encrypt_pwd(request.POST.get('db_password')),
                db_memo=request.POST.get('db_memo')
            )

            db.db_group.set(request.POST.getlist('db_group'))
            return JsonResponse({'code': 200, 'data': None, 'msg': '数据库添加成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'data': None, 'msg': '数据库添加失败！{}'.format(e)})


@admin_auth
def db_user(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        port = request.POST.get('port')
        action = request.POST.get('action')
        db_server = ServerAssets.objects.select_related('assets').get(id=pk)
        try:
            conn = MysqlPool(db_server.assets.asset_management_ip, int(port), settings.MYSQL_USER, settings.MYSQL_PASS,
                             'mysql')
            if action == 'show databases':
                res = conn.get_dbs()
                return JsonResponse({'code': 200, 'data': res, 'msg': 'sql执行成功！'})
            elif action == 'show users':
                res = conn.user_all()
                return JsonResponse({'code': 200, 'data': res, 'msg': 'sql执行成功！'})
            elif action == 'add user':
                user = request.POST.get('user').split('@')
                password = request.POST.get('password')
                db_table = request.POST.get('db_table', None)
                privs = request.POST.getlist('privs', None)
                conn.user_add(user[0], user[1], password, db_table, privs)
                return JsonResponse({'code': 200, 'data': None, 'msg': '用户添加成功！'})
            elif action == 'delete user':
                user = request.POST.get('user').split('@')
                conn.user_delete(user[0], user[1])
                return JsonResponse({'code': 200, 'data': None, 'msg': '用户删除成功！'})
            elif action == 'mod user':
                old_user = request.POST.get('old_user').split('@')
                new_user = request.POST.get('new_user').split('@')
                conn.user_mod(old_user[0], old_user[1], new_user=new_user[0], new_host=new_user[1])
                return JsonResponse({'code': 200, 'data': None, 'msg': '用户修改成功！'})
            elif action == 'mod pass':
                user = request.POST.get('user').split('@')
                password = request.POST.get('password')
                conn.user_mod(user[0], user[1], password=password)
                return JsonResponse({'code': 200, 'data': None, 'msg': '密码修改成功！'})
            elif action == 'add priv':
                user = request.POST.get('user').split('@')
                db_table = request.POST.get('db_table')
                privs = request.POST.getlist('privs')
                conn.privileges_grant(user[0], user[1], db_table, privs)
                return JsonResponse({'code': 200, 'data': None, 'msg': '权限添加成功！'})
            elif action == 'del priv':
                user = request.POST.get('user').split('@')
                db_table = request.POST.get('db_table')
                privs = request.POST.getlist('privs')
                conn.privileges_revoke(user[0], user[1], db_table, privs)
                return JsonResponse({'code': 200, 'data': None, 'msg': '权限删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'data': None, 'msg': 'sql执行失败！{}'.format(e)})

    privs = VALID_PRIVS
    server_assets = ServerAssets.objects.select_related('assets').all()
    return render(request, 'dbmanager/db_user.html', locals())


@admin_auth
def db_edit(request, pk):
    db = DBConfig.objects.select_related('db_server').get(id=pk)
    if request.method == 'GET':
        data = {
            'db_server': db.db_server_id,
            'db_port': db.db_port,
            'db_name': db.db_name,
            'db_user': db.db_user,
            'db_password': CryptPwd().decrypt_pwd(db.db_password),
            'db_group': [group.id for group in db.db_group.all()],
            'db_memo': db.db_memo
        }
        return JsonResponse({'code': 200, 'data': data})
    elif request.method == 'POST':
        try:
            db.db_port = int(request.POST.get('db_port'))
            db.db_name = request.POST.get('db_name')
            db.db_user = request.POST.get('db_user')
            db.db_password = CryptPwd().encrypt_pwd(request.POST.get('db_password'))
            db.db_memo = request.POST.get('db_memo')
            db.db_group.set(request.POST.getlist('db_group'))
            db.save()
            return JsonResponse({'code': 200, 'data': None, 'msg': '数据库更新成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'data': None, 'msg': '数据库更新失败！{}'.format(e)})


@admin_auth
def db_del(request, pk):
    if request.method == 'DELETE':
        try:
            DBConfig.objects.get(id=pk).delete()
            return JsonResponse({'code': 200, 'data': None, 'msg': '数据库删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'data': None, 'msg': '数据库删除失败！{}'.format(e)})


@permission_required('dbmanager.add_dblog', raise_exception=True)
def db_exec(request):
    if request.method == 'GET':
        all_dbs = DBConfig.objects.prefetch_related('db_group').all()
        user_groups = request.user.groups.all()

        user_dbs = []
        for db in all_dbs:
            if not set(db.db_group.all()).isdisjoint(set(user_groups)):
                user_dbs.append(db)
        dbs = all_dbs if request.user.is_superuser else user_dbs
        return render(request, 'dbmanager/db_exec.html', {'user_dbs': dbs})
    elif request.method == 'POST':
        pk = request.POST.get('pk')
        sql = request.POST.get('sql')
        sql_type = request.POST.get('sql_type')
        sql_file = request.FILES.get('upload_file')
        if sql_file:
            sql = ''.join({chunk.decode('utf-8') for chunk in sql_file.chunks(chunk_size=1024)})
            sql_file.close()
            return JsonResponse({'code': 200, 'data': sql, 'msg': 'sql上传成功！'})

        db = DBConfig.objects.select_related('db_server').get(id=pk)
        try:
            conn = MysqlPool(db.db_server.service_asset.asset_management_ip, db.db_port, db.db_user,
                             CryptPwd().decrypt_pwd(db.db_password), db.db_name)
            if sql == 'show tables':
                res = conn.get_tables(sql)
                return JsonResponse({'code': 200, 'data': res, 'msg': 'sql执行成功！'})
            elif sql_type == 'select':
                table_heads, res = conn.exec_select(sql)

                if isinstance(table_heads, list):
                    db_log_id = sql_log(db_config=db, db_login_user=request.user, db_sql_content=sql, db_sql_res=res,
                                        db_sql_res_thead=str(table_heads))
                    return JsonResponse({'code': 200, 'table_heads': table_heads, 'data': res, 'db_log_id': db_log_id,
                                         'msg': 'sql执行成功！'})
                else:
                    db_log_id = sql_log(db_config=db, db_login_user=request.user, db_sql_content=sql, db_sql_res=res)
                    return JsonResponse({'code': 507, 'data': res, 'db_log_id': db_log_id, 'msg': 'sql执行失败！'})
            elif sql_type == 'sql-one':
                res = conn.exec_sql_one(sql)
                db_sql_res = '受影响的行数: {}'.format(res) if isinstance(res, int) else str(res)
                db_log_id = sql_log(db_config=db, db_login_user=request.user, db_sql_content=sql,
                                    db_sql_res=db_sql_res)
                return JsonResponse(
                    {'code': 200, 'data': db_sql_res, 'db_log_id': db_log_id, 'msg': 'sql执行成功！'})
            elif sql_type == 'sql-many':
                sql_list = sql.split('args=')
                run_sql = sql_list[0].rstrip()
                args = eval(sql_list[1])
                res = conn.exec_sql_many(run_sql, args)
                db_log_id = sql_log(db_config=db, db_login_user=request.user, db_sql_content=sql,
                                    db_sql_res='受影响的行数: {}'.format(res))
                return JsonResponse(
                    {'code': 200, 'data': '受影响的行数: {}'.format(res), 'db_log_id': db_log_id, 'msg': 'sql执行成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'data': None, 'msg': 'sql执行失败！{}'.format(e)})


def sql_log(db_config, db_login_user, db_sql_content, db_sql_res, db_sql_res_thead=''):
    try:
        log = DBLog.objects.create(
            db_config=db_config,
            db_login_user=db_login_user,
            db_sql_content=db_sql_content,
            db_sql_res=db_sql_res,
            db_sql_res_thead=db_sql_res_thead
        )
        return log.id
    except Exception as e:
        logging.getLogger().error('添加SQL操作记录失败：{}'.format(e))


@permission_required('dbmanager.add_dblog', raise_exception=True)
def db_log(request):
    if request.method == 'GET':
        db_logs = DBLog.objects.select_related('db_config').all() if request.user.is_superuser else \
            DBLog.objects.select_related('db_config').filter(db_login_user=request.user)
        return render(request, 'dbmanager/db_log.html', locals())
    elif request.method == 'POST':
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        new_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
        end_time = new_end_time.strftime('%Y-%m-%d')
        try:
            records = []
            search_records = DBLog.objects.select_related('db_config').filter(db_run_datetime__gt=start_time,
                                                                              db_run_datetime__lt=end_time)
            for search_record in search_records:
                record = {
                    'id': search_record.id,
                    'db_project': '{}|{}'.format(search_record.db_config.db_server.project.project_name,
                                                 search_record.db_config.db_server.project.get_project_env_display()),
                    'db_server': '{}|{}'.format(search_record.db_config.db_server.service_asset.asset_management_ip,
                                                search_record.db_config.db_name),
                    'db_sql_content': search_record.db_sql_content,
                    'db_sql_res': search_record.db_sql_res,
                    'db_sql_res_thead': search_record.db_sql_res_thead,
                    'db_login_user': search_record.db_login_user.username,
                    'db_run_datetime': search_record.db_run_datetime,
                }
                records.append(record)
            return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})


@permission_required('dbmanager.add_dblog', raise_exception=True)
def db_log_detail(request):
    pk = request.GET.get('pk') if request.GET.get('pk') else request.POST.get('pk')
    log = DBLog.objects.get(id=pk)
    res = eval(log.db_sql_res)
    data = [list(i) for i in res]
    heads = eval(log.db_sql_res_thead)

    if request.method == 'POST':
        return JsonResponse({'code': 200, 'heads': heads, 'data': data})
    elif request.method == 'GET':
        filename = 'query_res.csv'

        try:
            with codecs.open(filename, 'w+', 'utf_8_sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(heads)
                writer.writerows(data)

            response = FileResponse(open(filename, 'rb'))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{filename}"'.format(filename=filename)
            return response
        except Exception as e:
            logging.getLogger().error('导出sql查询结果失败：{}'.format(e))
