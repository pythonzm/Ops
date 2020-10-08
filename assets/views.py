import uuid
import datetime
import json
import os
import re
import xlrd
import xlwt
import logging
from ast import literal_eval
from itertools import product
from utils.export_excel import ExportExcel
from django.conf import settings
from django.db.models import Count
from django.core import serializers
from django.http import JsonResponse, FileResponse
from django.shortcuts import render
from assets.models import *
from assets.utils.ali_api import AliAPI
from users.models import UserProfile
from utils.crypt_pwd import CryptPwd
from task.utils.ansible_api_v2 import ANSRunner
from django.contrib.auth.decorators import permission_required
from utils.sftp import SFTP
from utils.decorators import admin_auth


@permission_required('assets.add_assets', raise_exception=True)
def get_assets_charts(request):
    assets_count = Assets.objects.all().count()
    online_assets_count = Assets.objects.filter(asset_status=0).count()
    break_assets_count = Assets.objects.filter(asset_status=2).count()
    unused_assets_count = Assets.objects.filter(asset_status=3).count()

    asset_data = []
    data_detail = []
    asset_types_count = Assets.objects.values('asset_type').annotate(dcount=Count('asset_type'))
    for m, n in product(asset_types_count, Assets.asset_types):
        if m.get('asset_type') == n[0]:
            asset_data.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    server_types_count = ServerAssets.objects.values('server_type').annotate(dcount=Count('server_type'))
    for m, n in product(server_types_count, ServerAssets.server_types):
        if m.get('server_type') == n[0]:
            data_detail.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    network_types_count = NetworkAssets.objects.values('network_type').annotate(dcount=Count('network_type'))
    for m, n in product(network_types_count, NetworkAssets.network_types):
        if m.get('network_type') == n[0]:
            data_detail.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    office_types_count = OfficeAssets.objects.values('office_type').annotate(dcount=Count('office_type'))
    for m, n in product(office_types_count, OfficeAssets.office_types):
        if m.get('office_type') == n[0]:
            data_detail.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    security_types_count = SecurityAssets.objects.values('security_type').annotate(dcount=Count('security_type'))
    for m, n in product(security_types_count, SecurityAssets.security_types):
        if m.get('security_type') == n[0]:
            data_detail.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    storage_types_count = StorageAssets.objects.values('storage_type').annotate(dcount=Count('storage_type'))
    for m, n in product(storage_types_count, StorageAssets.storage_types):
        if m.get('storage_type') == n[0]:
            data_detail.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    software_types_count = SoftwareAssets.objects.values('software_type').annotate(dcount=Count('software_type'))
    for m, n in product(software_types_count, SoftwareAssets.software_types):
        if m.get('software_type') == n[0]:
            data_detail.append({'asset_type': n[1], 'dcount': m.get('dcount')})

    admin_records = AdminRecord.objects.select_related('admin_login_user').all().order_by('-admin_start_time')[:5]

    return render(request, 'assets/assets_charts.html', locals())


@permission_required('assets.add_assets', raise_exception=True)
def get_assets_list(request):
    asset_types = Assets.asset_types
    asset_status = request.GET.get('asset_status')
    assets = None
    if asset_status:
        db_status = tuple(filter(lambda x: x[1] == asset_status, Assets.asset_status_))[0][0]
        assets = Assets.objects.filter(asset_status=db_status)
    else:
        assets = Assets.objects.select_related('serverassets')
    return render(request, 'assets/assets_list.html', locals())


@permission_required('assets.add_assets', raise_exception=True)
def add_asset(request):
    asset_types = Assets.asset_types
    server_types = ServerAssets.server_types
    network_types = NetworkAssets.network_types
    office_types = OfficeAssets.office_types
    security_types = SecurityAssets.security_types
    storage_types = StorageAssets.storage_types
    software_types = SoftwareAssets.software_types
    asset_status_ = Assets.asset_status_
    asset_providers = AssetProvider.objects.all()
    asset_admins = UserProfile.objects.all()
    asset_idcs = IDC.objects.all()
    asset_cabinets = Cabinet.objects.select_related('idc')
    server_assets = ServerAssets.objects.select_related('assets')
    return render(request, 'assets/add_asset.html', locals())


@permission_required('assets.add_assets', raise_exception=True)
def add_base_asset(request):
    asset_idcs = IDC.objects.all()
    asset_cabinets = Cabinet.objects.select_related('idc')
    asset_providers = AssetProvider.objects.all()
    return render(request, 'assets/add_base_asset.html', locals())


@permission_required('assets.add_assets', raise_exception=True)
def update_asset(request, asset_type, pk):
    if request.method == 'GET':
        asset = Assets.objects.get(id=pk)
        asset_types = Assets.asset_types
        asset_status_ = Assets.asset_status_
        asset_admins = UserProfile.objects.all()
        asset_providers = AssetProvider.objects.all()
        asset_idcs = IDC.objects.all()
        if asset_type == 'server':
            password = CryptPwd().decrypt_pwd(asset.serverassets.password)
            server_assets = ServerAssets.objects.select_related('assets')
        return render(request, 'assets/update_asset.html', locals())
    elif request.method == 'POST':
        if asset_type == 'server':
            if request.POST.get('host_vars'):
                server_obj = ServerAssets.objects.filter(id=pk)
                if request.POST.get('host_vars') == 'null':
                    server_obj.update(host_vars='')
                else:
                    server_obj.update(host_vars=request.POST.get('host_vars'))
                msg = ServerAssets.objects.get(id=pk).assets.asset_management_ip
                return JsonResponse({'code': 200, 'msg': msg})
            else:
                asset = Assets.objects.get(id=pk)
                ServerAssets.objects.filter(id=asset.serverassets.id).update(
                    username=request.POST.get('username'),
                    password=CryptPwd().encrypt_pwd(request.POST.get('password')),
                    port=request.POST.get('port'),
                    system=request.POST.get('system')
                )
                return JsonResponse({'code': 200, 'msg': '修改成功'})
        return JsonResponse({'code': 200, 'msg': '修改成功'})


@permission_required('assets.add_assets', raise_exception=True)
def server_facts(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        module = request.POST.get('module')
        server_obj = ServerAssets.objects.select_related('assets').get(id=pk)
        resource = [{"ip": server_obj.assets.asset_management_ip, "port": int(server_obj.port),
                     "username": server_obj.username,
                     "password": CryptPwd().decrypt_pwd(server_obj.password)}]

        try:
            ans = ANSRunner(resource, become='yes', become_method='sudo', become_user='root')
            ans.run_module(host_list=[server_obj.assets.asset_management_ip], module_name=module, module_args="")

            for data in ans.get_module_results:
                if module == 'setup':
                    if 'success' in data:
                        server_info, server_model, nks = handle_setup_data(data)
                        Assets.objects.filter(id=server_obj.assets_id).update(
                            asset_model=server_model
                        )
                        ServerAssets.objects.select_related('assets').filter(id=pk).update(**server_info)

                        asset = Assets.objects.get(id=server_obj.assets_id)
                        for nk in nks:
                            mac = nk.get('network_card_mac')
                            NetworkCardAssets.objects.select_related('asset').update_or_create(defaults=nk, asset=asset,
                                                                                               network_card_mac=mac)
                        return JsonResponse({'code': 200, 'msg': '收集完成！'})
                    else:
                        return JsonResponse({'code': 500, 'msg': '收集失败！{}'.format(data[data.index('>>') + 1:])})
                elif module == 'get_mem':
                    if 'success' in data:
                        mem_infos = handle_mem_data(data)

                        asset = Assets.objects.get(id=server_obj.assets_id)
                        for mem_info in mem_infos:
                            ram_slot = mem_info.get('ram_slot')
                            RamAssets.objects.select_related('asset').update_or_create(defaults=mem_info, asset=asset,
                                                                                       ram_slot=ram_slot)
                        return JsonResponse({'code': 200, 'msg': '收集完成！'})
                    else:
                        return JsonResponse({'code': 500, 'msg': '收集失败！{}'.format(data[data.index('>>') + 1:])})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': str(e)})


@permission_required('assets.add_assets', raise_exception=True)
def get_asset_info(request, pk):
    asset = Assets.objects.get(id=pk)
    return render(request, 'assets/asset_info.html', locals())


@permission_required('assets.add_assets', raise_exception=True)
def import_assets(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        filename = os.path.join(settings.BASE_DIR, 'upload', file.name)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        try:
            xl_file = xlrd.open_workbook(filename)
            sheet_names = xl_file.sheet_names()
            data_list = []
            for sheet_name in sheet_names:
                sheet_obj = xl_file.sheet_by_name(sheet_name)
                for i in range(1, sheet_obj.nrows):
                    data_list.append(sheet_obj.row_values(i))

            for data in data_list:
                assets = {
                    'asset_type': data[0],
                    'asset_nu': data[1],
                    'asset_model': data[2] if data[2] else None,
                    'asset_provider': AssetProvider.objects.get(id=int(data[3])) if data[3] else None,
                    'asset_status': int(data[4]) if data[4] else 0,
                    'asset_management_ip': data[5] if data[5] else None,
                    'asset_admin': UserProfile.objects.get(id=int(data[6])) if data[6] else UserProfile.objects.get(
                        username=request.user),
                    'asset_idc': IDC.objects.get(id=int(data[7])) if data[7] else None,
                    'asset_cabinet': Cabinet.objects.select_related('idc').get(id=int(data[8])) if data[8] else None,
                    'asset_purchase_day': xlrd.xldate_as_datetime(data[9], 0),
                    'asset_expire_day': xlrd.xldate_as_datetime(data[10], 0),
                    'asset_price': data[11] if data[11] else None,
                    'asset_memo': data[12],
                }
                asset_obj, created = Assets.objects.update_or_create(asset_nu=data[1], defaults=assets)

                if data[0] == 'server':
                    server_asset = {
                        'server_type': int(data[13]),
                        'username': data[14],
                        'password': CryptPwd().encrypt_pwd(str(data[15])) if data[15] else None,
                        'port': int(data[16]),
                        'system': data[17],
                        'hosted_on': ServerAssets.objects.select_related('assets').get(id=int(data[18])) if data[
                            18] else None,
                    }
                    ServerAssets.objects.update_or_create(assets=asset_obj, defaults=server_asset)
                elif data[0] == 'network':
                    NetworkAssets.objects.update_or_create(assets=asset_obj, network_type=int(data[13]))
                elif data[0] == 'office':
                    OfficeAssets.objects.update_or_create(assets=asset_obj, office_type=int(data[13]))
                elif data[0] == 'security':
                    SecurityAssets.objects.update_or_create(assets=asset_obj, security_type=int(data[13]))
                elif data[0] == 'storage':
                    StorageAssets.objects.update_or_create(assets=asset_obj, storage_type=int(data[13]))
                elif data[0] == 'software':
                    SoftwareAssets.objects.update_or_create(assets=asset_obj, software_type=int(data[13]))
            return JsonResponse({'code': 200, 'msg': '导入成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '导入失败！，{}'.format(e)})


@permission_required('assets.add_assets', raise_exception=True)
def export_assets(request):
    if request.method == 'POST':
        pks = request.POST.get('pks')
        server_row = network_row = office_row = security_row = storage_row = software_row = 1
        excel = None
        filename = '资产列表.csv'
        try:
            file = xlwt.Workbook(encoding='utf-8', style_compression=0)

            # 生成sheet
            server_sheet = file.add_sheet('server', cell_overwrite_ok=True)
            network_sheet = file.add_sheet('network', cell_overwrite_ok=True)
            office_sheet = file.add_sheet('office', cell_overwrite_ok=True)
            security_sheet = file.add_sheet('security', cell_overwrite_ok=True)
            storage_sheet = file.add_sheet('storage', cell_overwrite_ok=True)
            software_sheet = file.add_sheet('software', cell_overwrite_ok=True)

            # 导出数据
            for pk in json.loads(pks):
                asset = Assets.objects.get(id=int(pk))

                if asset.asset_type == 'server':
                    excel = ExportExcel(filename, excel_obj=file, asset_obj=asset, sheet_name=server_sheet)
                    excel.gen_body(server_row)
                    server_row = server_row + 1
                elif asset.asset_type == 'network':
                    excel = ExportExcel(filename, excel_obj=file, asset_obj=asset, sheet_name=network_sheet)
                    excel.gen_body(network_row)
                    network_row = network_row + 1
                elif asset.asset_type == 'office':
                    excel = ExportExcel(filename, excel_obj=file, asset_obj=asset, sheet_name=office_sheet)
                    excel.gen_body(office_row)
                    office_row = office_row + 1
                elif asset.asset_type == 'security':
                    excel = ExportExcel(filename, excel_obj=file, asset_obj=asset, sheet_name=security_sheet)
                    excel.gen_body(security_row)
                    security_row = security_row + 1
                elif asset.asset_type == 'storage':
                    excel = ExportExcel(filename, excel_obj=file, asset_obj=asset, sheet_name=storage_sheet)
                    excel.gen_body(storage_row)
                    storage_row = storage_row + 1
                elif asset.asset_type == 'software':
                    excel = ExportExcel(filename, excel_obj=file, asset_obj=asset, sheet_name=software_sheet)
                    excel.gen_body(software_row)
                    software_row = software_row + 1
                excel.gen_headers()
            excel.save_excel()
            response = FileResponse(excel.download_excel())
            response['Content-Type'] = 'application/octet-stream'
            response['charset'] = 'utf-8'
            response['Content-Disposition'] = 'attachment;filename="{filename}"'.format(filename=filename)
            return response
        except Exception as e:
            logging.getLogger().error('导出失败！{}'.format(e))


@admin_auth
def ssh_terminal(request, pk):
    server_obj = ServerAssets.objects.select_related('assets').get(id=pk)
    ssh_server_ip = server_obj.assets.asset_management_ip

    if request.method == 'GET':
        download_file = request.GET.get('download_file')
        if download_file:
            download_file_path = os.path.join(settings.MEDIA_ROOT, 'admin_files', request.user.username, 'download',
                                              ssh_server_ip)

            sftp = SFTP(ssh_server_ip, server_obj.port, server_obj.username,
                        CryptPwd().decrypt_pwd(server_obj.password))

            response = sftp.download_file(download_file, download_file_path)
            return response
        else:
            remote_ip = request.META.get('REMOTE_ADDR')
            return render(request, 'assets/ssh_terminal.html', locals())
    elif request.method == 'POST':
        try:
            upload_file = request.FILES.get('upload_file')
            upload_file_path = os.path.join(settings.MEDIA_ROOT, 'fort_files', request.user.username, 'upload',
                                            server_obj.assets.asset_management_ip)
            sftp = SFTP(ssh_server_ip, server_obj.port, server_obj.username,
                        CryptPwd().decrypt_pwd(server_obj.password))
            sftp.upload_file(upload_file, upload_file_path)

            return JsonResponse({'code': 200, 'msg': '上传成功！文件默认放在{}用户家目录下'.format(server_obj.username)})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '上传失败！{}'.format(e)})


@admin_auth
def guacamole_terminal(request, pk):
    group_name = str(uuid.uuid4())
    server_obj = ServerAssets.objects.select_related('assets').get(id=pk)
    guacamole_server_ip = server_obj.assets.asset_management_ip
    remote_ip = request.META.get('REMOTE_ADDR')
    return render(request, 'assets/admin_guacamole.html', locals())


@admin_auth
def login_record(request):
    if request.method == 'GET':
        results = AdminRecord.objects.select_related('admin_login_user').all()
        return render(request, 'assets/login_admin_record.html', locals())
    elif request.method == 'POST':
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        new_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
        end_time = new_end_time.strftime('%Y-%m-%d')
        try:
            records = []
            search_records = AdminRecord.objects.select_related('admin_login_user').filter(
                admin_start_time__gt=start_time,
                admin_start_time__lt=end_time)
            for search_record in search_records:
                record = {
                    'id': search_record.id,
                    'admin_login_user': search_record.admin_login_user.username,
                    'admin_server': search_record.admin_server,
                    'admin_remote_ip': search_record.admin_remote_ip,
                    'admin_start_time': search_record.admin_start_time,
                    'admin_login_status_time': search_record.admin_login_status_time,
                    'admin_record_mode': search_record.get_admin_record_mode_display(),
                    'admin_record_cmds': search_record.admin_record_cmds
                }
                records.append(record)
            return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})


@admin_auth
def admin_play(request, pk):
    record = AdminRecord.objects.select_related('admin_login_user').get(id=pk)
    if record.admin_record_mode == 'ssh':
        return render(request, 'assets/ssh_play.html', locals())
    else:
        return render(request, 'assets/guacamole_play.html', locals())


@admin_auth
def update_pwd(request):
    if request.method == 'POST':
        pks = request.POST.getlist('pks')
        pwd = request.POST.get('pwd')

        try:
            for pk in pks:
                server = Assets.objects.get(id=pk).serverassets
                server.password = CryptPwd().encrypt_pwd(pwd)
                server.save()
            return JsonResponse({'code': 200, 'msg': '更新完毕!'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '更新失败：{}'.format(e)})


@admin_auth
def monitor(request, pk):
    return render(request, 'assets/monitor.html', {'pk': pk})


@admin_auth
def get_top_data(request, pk):
    server_obj = ServerAssets.objects.select_related('assets').get(id=pk)
    resource = [{"ip": server_obj.assets.asset_management_ip, "port": int(server_obj.port),
                 "username": server_obj.username,
                 "password": CryptPwd().decrypt_pwd(server_obj.password)}]

    ans = ANSRunner(resource, become='yes', become_method='sudo', become_user='root')
    ans.run_module(host_list=[server_obj.assets.asset_management_ip], module_name='shell',
                   module_args='export COLUMNS\=400 && top -bcn 1 && df -h -t ext3 -t ext4 -t xfs')
    result = ans.get_module_results[0]
    if 'success' in result:
        load, tasks, cpu, mem, swap, heads, body, disk = handle_top_data(result)
        return JsonResponse({'code': 200, 'data': {'load': load, 'tasks': tasks, 'cpu': cpu, 'mem': mem, 'swap': swap,
                                                   'heads': heads, 'body': body, 'disk': disk}, 'msg': '收集成功！'})
    else:
        return JsonResponse({'code': 500, 'msg': '收集失败！{}'.format(result[result.index('>>') + 1:])})


def handle_setup_data(data):
    """处理setup模块数据，用于收集服务器信息功能"""
    server_info = {}
    result = json.loads(data[data.index('{'): data.rindex('}') + 1])
    facts = result['ansible_facts']
    server_info['hostname'] = facts['ansible_hostname']
    server_info['cpu_model'] = facts['ansible_processor'][-1]
    server_info['cpu_number'] = int(facts['ansible_processor_count'])
    server_info['vcpu_number'] = int(facts['ansible_processor_vcpus'])
    server_info['disk_total'], disk_size = 0, 0
    for k, v in facts['ansible_devices'].items():
        if k[0:2] in ['sd', 'hd', 'ss', 'vd']:
            if 'G' in v['size']:
                disk_size = float(v['size'][0: v['size'].rindex('G') - 1])
            elif 'T' in v['size']:
                disk_size = float(v['size'][0: v['size'].rindex('T') - 1]) * 1024
            server_info['disk_total'] += round(disk_size, 2)
    server_info['ram_total'] = round(int(facts['ansible_memtotal_mb']) / 1024)
    server_info['kernel'] = facts['ansible_kernel']
    server_model = facts['ansible_product_name']

    # 获取网卡信息
    nks = []
    for nk in facts.keys():
        networkcard_facts = {}
        if re.match(r"^ansible_(eth|bind|eno|ens|em)\d+?", nk):
            networkcard_facts['network_card_name'] = facts.get(nk).get('device')
            networkcard_facts['network_card_mac'] = facts.get(nk).get('macaddress')
            networkcard_facts['network_card_ip'] = facts.get(nk).get('ipv4').get('address') if 'ipv4' in facts.get(
                nk) else 'unknown'
            networkcard_facts['network_card_model'] = facts.get(nk).get('type')
            networkcard_facts['network_card_mtu'] = facts.get(nk).get('mtu')
            networkcard_facts['network_card_status'] = 1 if facts.get(nk).get('active') else 0
            nks.append(networkcard_facts)
    return server_info, server_model, nks


def handle_mem_data(data):
    """
    处理获取的内存信息
    :param data: 通过ansible获取的内存信息
    :return:
    """
    result = json.loads(data[data.index('{'): data.rindex('}') + 1])
    facts = result['ansible_facts']
    return facts['mem_info']


def handle_top_data(data):
    """
    处理获取的top命令信息
    :param data: 通过ansible获取的top命令信息
    :return:
    """
    result = data[data.index('top'): data.index('</code>')]
    r = [i for i in result.split('\n') if len(i) > 0]

    load = [i.strip() for i in r[0].split('load average:')[1].split(',')]

    t = r[1].split(':')[1]
    tasks = ((n for n in m.split()) for m in t.split(','))
    tasks = dict((y, x) for x, y in tasks)

    c = r[2].split(':')[1]
    cpu = ((n for n in m.replace('%', ' ').split()) for m in c.split(','))
    cpu = dict((y, x) for x, y in cpu)

    m = r[3].split(':')[1]
    mem = ((n for n in re.sub('k', '', re.sub('\+', '0 ', i)).split()) for i in m.split(','))
    mem = dict((y, x) for x, y in mem)

    s = re.sub('avail Mem', 'availableMem', r[4].split(':')[1])
    swap = ((n for n in re.sub('k', '', i).split()) for i in re.sub(r'\.', ',', s).split(','))
    swap = dict((y, x) for x, y in swap)

    heads = None
    for i in r:
        if i.lstrip().startswith('P'):
            heads = [h for h in i.split()]
            break

    p = [d.strip() for d in r if d.lstrip()[0].isdigit() and d.rstrip()[-1] != ']']
    body = [[n for n in x.split()[:len(heads) - 1] + [' '.join(x.split()[len(heads) - 1:])]] for x in p]

    d = [i for i in r if i.lstrip().startswith('/') and 'boot' not in i]
    disk = [['disk', '总容量', '已用', '可用']]
    for i in d:
        # disk = [f'{i.split()[0]}({(i.split()[-1])})'].extend(i.split()[1:-2])
        temp = [format_size(n) for n in i.split()[1:-2]]
        temp.insert(0, i.split()[-1])
        disk.append(temp)

    return load, tasks, cpu, mem, swap, heads, body, disk


def format_size(size):
    if size.endswith('M'):
        size = round(int(size[:-1]) / 1024, 2)
    elif size.endswith('T'):
        size = int(size[:-1]) * 1024
    else:
        size = float(size[:-1])

    return size


@admin_auth
def pull_asset(request):
    if request.method == 'POST':
        test_auth = request.POST.get('test_auth')
        conf_ids = request.POST.get('conf_ids')

        if test_auth:
            access_id = request.POST.get('access_id')
            access_key = request.POST.get('access_key')
            cloud_region = request.POST.get('cloud_region')

            ali = AliAPI(access_id, access_key, cloud_region)
            error_msg = ali.test_auth()
            return JsonResponse({'code': 200, 'msg': error_msg})
        if conf_ids:
            conf_ids = literal_eval(conf_ids)
            for conf_id in conf_ids:
                conf_obj = PullAssetConf.objects.get(id=conf_id)
                ali = AliAPI(conf_obj.access_id, conf_obj.access_key, conf_obj.cloud_region)
                try:
                    ali.sync_to_cmdb(conf_obj)
                except Exception as e:
                    return JsonResponse({'code': 500, 'msg': f'数据同步失败！{e}'})
            return JsonResponse({'code': 200, 'msg': '数据同步完成！'})
    cloud_names = PullAssetConf.cloud_names
    pull_asset_confs = PullAssetConf.objects.all()
    users = UserProfile.objects.values_list('id', 'username')
    return render(request, 'assets/pull_asset.html', locals())
