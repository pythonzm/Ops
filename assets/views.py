from django.shortcuts import render
from assets.models import *


def get_assets_charts(request):
    assets_count = Assets.objects.all().count()
    online_assets_count = Assets.objects.filter(asset_status=0).count()
    break_assets_count = Assets.objects.filter(asset_status=2).count()
    unused_assets_count = Assets.objects.filter(asset_status=3).count()
    return render(request, 'assets/assets_charts.html', locals())
