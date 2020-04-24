import json
import logging
from assets.models import Assets, ServerAssets, IDC, Cabinet, AssetProvider
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest


class AliAPI:
    def __init__(self, access_id, access_key, region):
        self.access_id = access_id
        self.access_key = access_key
        self.region = region
        self.client = self.create_client()
        self.page_number = 1  # 实例状态列表的页码。起始值：1 默认值：1
        self.page_size = 10  # 分页查询时设置的每页行数。最大值：100 默认值：10

    def create_client(self):
        client = AcsClient(self.access_id, self.access_key, self.region)
        return client

    def set_request(self):
        request = DescribeInstancesRequest()
        request.set_accept_format('json')
        request.set_PageNumber(self.page_number)
        request.set_PageSize(self.page_size)
        return request

    def test_auth(self):
        """
        测试接口权限等信息是否异常
        :return:
        """
        error_msg = None
        self.page_number = 1
        self.page_size = 1
        request = self.set_request()
        try:
            self.client.do_action_with_exception(request)
        except Exception as e:
            error_msg = f'{e}'
        return error_msg

    def get_response(self):
        """
        获取返回值
        :return:
        """
        request = self.set_request()
        response = self.client.do_action_with_exception(request)
        return str(response, encoding='utf-8')

    def gen_server_info(self, conf_obj):
        try:
            response = self.get_response()
        except Exception as e:
            logging.getLogger().error(f'拉取服务器信息失败：{e}')
            return False

        res = json.loads(response)['Instances']['Instance']
        server_list = []
        for i in res:
            asset_data = {}
            server_data = {}

            idc, cabinet, asset_provider = self.gen_base_info(i)

            # 内网IP
            try:
                # VPC里面内网IP
                private_ip = i['VpcAttributes']['PrivateIpAddress']['IpAddress'][0]
            except (KeyError, IndexError):
                # 非VPC里面获取内网IP
                private_ip = i['InnerIpAddress']['IpAddress'][0]

            # 公网IP/弹性IP
            try:
                asset_data['asset_management_ip'] = i['PublicIpAddress']['IpAddress'][0]
            except(KeyError, IndexError):
                asset_data['asset_management_ip'] = i['EipAddress']['IpAddress']
            except Exception:
                asset_data['asset_management_ip'] = private_ip

            asset_data['asset_type'] = 'server'
            asset_data['asset_nu'] = i.get('InstanceId')
            asset_data['asset_model'] = 'Alibaba Cloud ECS'
            asset_data['asset_status'] = 0 if i.get('Status').lower() == 'running' else 2
            asset_data['asset_purchase_day'] = i.get('CreationTime').split('T')[0]
            asset_data['asset_expire_day'] = i.get('ExpiredTime').split('T')[0]
            asset_data['asset_admin_id'] = conf_obj.belong_user_id
            asset_data['asset_provider'] = asset_provider
            asset_data['asset_idc'] = idc
            asset_data['asset_cabinet'] = cabinet

            server_data['server_type'] = 2
            server_data['username'] = conf_obj.server_user
            server_data['password'] = conf_obj.server_user_password
            server_data['port'] = conf_obj.server_port
            try:
                server_data['hostname'] = i.get('InstanceName')
            except(KeyError, TypeError):
                server_data['hostname'] = i.get('InstanceId')  # 取不到给instance_id
            server_data['vcpu_number'] = i.get('Cpu')
            server_data['ram_total'] = i.get('Memory') / 1024
            server_data['system'] = i.get("OSType")
            server_data['system_version'] = i.get("OSName")

            server_list.append([asset_data, server_data])
        return server_list

    def sync_to_cmdb(self, conf_obj):
        server_list = self.gen_server_info(conf_obj)
        for server in server_list:
            asset, _ = Assets.objects.update_or_create(defaults=server[0], asset_nu=server[0].get('asset_nu'))
            ServerAssets.objects.select_related('assets').update_or_create(defaults=server[1], assets_id=asset.id)

    def gen_base_info(self, server_info):
        """
        将机房和供应商设置为云厂商名称，机柜设置为区域ID
        :return:
        """
        idc, _ = IDC.objects.get_or_create(defaults={'idc_name': 'ali'}, idc_name='ali')

        zone_id = server_info.get('ZoneId')
        c = {'idc': idc, 'cabinet_name': zone_id}
        cabinet, _ = Cabinet.objects.get_or_create(defaults=c, cabinet_name=zone_id)

        asset_provider, _ = AssetProvider.objects.get_or_create(defaults={'asset_provider_name': 'ali'},
                                                                   asset_provider_name='ali')
        return idc, cabinet, asset_provider
