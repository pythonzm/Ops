from django.http import HttpResponse
from django.shortcuts import render
from scanhosts.utils.get_scan_results import get_scan_results
from conf.logger import scanhost_logger
from django.views.decorators.csrf import csrf_exempt
from scanhosts.models import HostInfo
from utils.init_yaml import Yaml
import yaml
from django.core import serializers
from utils.get_verbose_name import get_model_fields


@csrf_exempt
def result(request):
    """
    扫描主机信息，并将信息保存至数据库，并将主机加入黑名单表示以后不再扫描
    :param request:
    :return:
    """
    if request.method == 'POST':
        results = get_scan_results()
        scanhost_logger.info('获取数据完成！开始保存至扫描数据库！')
        conf = Yaml('scanhosts.yaml').init_yaml()
        black_list = conf['hostinfo']['black_list']
        try:
            for hostinfo in results:
                HostInfo.objects.update_or_create(**hostinfo)
                scanhost_logger.info('{}的数据保存数据库完成！'.format(hostinfo['internal_ip']))
                if hostinfo['internal_ip'] in black_list:
                    pass
                else:
                    black_list.append(hostinfo['internal_ip'])
            with open(Yaml('scanhosts.yaml').file, 'w+') as f:
                conf['hostinfo']['black_list'] = list(set(black_list))
                yaml.dump(conf, f, default_flow_style=False)
                scanhost_logger.info('更新scanhosts.yaml文件完成，扫描任务结束')
            results = HostInfo.objects.all()
            results = serializers.serialize('json', results)
            return HttpResponse(results)
        except Exception as e:
            scanhost_logger.error('数据保存出错，原因：{}'.format(e))
    else:
        fields = get_model_fields(HostInfo)
        return render(request, 'scanhost/scan_results.html', locals())


def scan_history(request):
    fields = get_model_fields(HostInfo)
    hostinfos = HostInfo.objects.all()
    return render(request, 'scanhost/scan_history.html', locals())


def scan_detail(request, pk):
    hostinfo = HostInfo.objects.get(id=pk)
    fields = get_model_fields(HostInfo)
    return render(request, 'scanhost/scan_detail.html', locals())


def test(request):
    fields = get_model_fields(HostInfo)
    r = HostInfo.objects.all()
    return render(request, 'test/test.html', locals())
