from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from assets.models import *
from users.models import UserProfile
from django.core import serializers


def get_assets_charts(request):
    assets = Assets.objects.all()
    asset_types = Assets.asset_types
    online_assets_count = Assets.objects.filter(asset_status=0).count()
    break_assets_count = Assets.objects.filter(asset_status=2).count()
    unused_assets_count = Assets.objects.filter(asset_status=3).count()
    asset_types_count = Assets.objects.values('asset_type').annotate(dcount=Count('asset_type'))
    asset_logs = AssetsLog.objects.all().order_by('-c_time')[:6]

    return render(request, 'assets/assets_charts.html', locals())


def get_assets_list(request):
    assets = Assets.objects.all().select_related()
    asset_types = Assets.asset_types
    return render(request, 'assets/assets_list.html', locals())


def add_asset(request):
    asset_types = Assets.asset_types
    server_types = ServerAssets.server_types
    network_types = NetworkAssets.network_types
    office_types = OfficeAssets.office_types
    security_types = SecurityAssets.security_types
    storage_types = StorageAssets.storage_types
    software_types = SoftwareAssets.software_types
    asset_status_ = Assets.asset_status_
    asset_providers = AssetProvider.objects.all().select_related()
    asset_admins = UserProfile.objects.all().select_related()
    asset_idcs = IDC.objects.all().select_related()
    asset_cabinets = Cabinet.objects.all().select_related()
    auth_types = ServerAssets.auth_types
    server_assets = ServerAssets.objects.all().select_related()
    return render(request, 'assets/add_asset.html', locals())


def add_base_asset(request):
    asset_idcs = IDC.objects.all().select_related()
    asset_cabinets = Cabinet.objects.all().select_related()
    asset_providers = AssetProvider.objects.all().select_related()
    return render(request, 'assets/add_base_asset.html', locals())


def update_asset(request, asset_type, pk):
    asset = Assets.objects.get(id=pk)
    if request.method == 'GET':
        asset_types = Assets.asset_types
        auth_types = ServerAssets.auth_types
        asset_status_ = Assets.asset_status_
        asset_admins = UserProfile.objects.all().select_related()
        asset_providers = AssetProvider.objects.all().select_related()
        asset_idcs = IDC.objects.all().select_related()
        server_assets = ServerAssets.objects.all().select_related()
        return render(request, 'assets/update_asset.html', locals())
    elif request.method == 'PUT':
        if asset_type == 'server':
            ServerAssets.objects.filter(id=asset.serverassets.id).update(
                username=request.POST.get('username'),
                auth_type=request.POST.get('auth_type'),
                password=request.POST.get('password'),
                port=request.POST.get('port')
            )
            return JsonResponse({'code': 200, 'msg': '修改成功'})
        return JsonResponse({'code': 200, 'msg': '修改成功'})


def get_assets_log(request):
    if request.method == 'GET':
        assets_logs = AssetsLog.objects.all()
        return render(request, 'assets/assets_log.html', locals())
    elif request.method == 'POST':
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        try:
            assets_logs = AssetsLog.objects.filter(c_time__gte=start_time, c_time__lte=end_time)
            assets_logs = serializers.serialize('json', assets_logs)
            return HttpResponse(assets_logs)
        except Exception as e:
            return JsonResponse({'error': '查询失败：{}'.format(e)})


def assets_search(request, key):
    assets = Assets.objects.all().select_related()
    asset_types = Assets.asset_types
    return render(request, 'assets/assets_search.html', locals())