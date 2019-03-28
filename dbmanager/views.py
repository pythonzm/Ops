import csv
import logging
import datetime
from utils.db.mysql_ops import MysqlPool
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from dbmanager.models import DBConfig, DBLog
from projs.models import Service
from django.contrib.auth.models import Group
from utils.decorators import admin_auth
from utils.crypt_pwd import CryptPwd
from django.contrib.auth.decorators import permission_required


@admin_auth
def db_list(request):
    if request.method == 'GET':
        dbs = DBConfig.objects.select_related('db_server').all()
        services = Service.objects.select_related('project').select_related('service_asset').all()
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
        dbs = DBConfig.objects.prefetch_related('db_group').all()
        user_groups = request.user.groups.all()

        user_dbs = []
        for db in dbs:
            if not set(db.db_group.all()).isdisjoint(set(user_groups)):
                user_dbs.append(db)
        return render(request, 'dbmanager/db_exec.html', {'user_dbs': user_dbs})
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
        db_logs = DBLog.objects.select_related('db_config').all()
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
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(heads)
                writer.writerows(data)

            response = FileResponse(open(filename, 'rb'))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{filename}"'.format(filename=filename)
            return response
        except Exception as e:
            logging.getLogger().error('导出sql查询结果失败：{}'.format(e))
