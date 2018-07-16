from django.db.models import Count
from django.shortcuts import render
from assets.models import *


def get_assets_charts(request):
    assets = Assets.objects.all()
    online_assets_count = Assets.objects.filter(asset_status=0).count()
    break_assets_count = Assets.objects.filter(asset_status=2).count()
    unused_assets_count = Assets.objects.filter(asset_status=3).count()
    asset_types = Assets.objects.values('asset_type').annotate(dcount=Count('asset_type'))
    print(asset_types)
    return render(request, 'assets/assets_charts.html', locals())
