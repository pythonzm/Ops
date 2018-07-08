# -*- coding: utf-8 -*-

from scanhosts.models import HostInfo
from ansible_task.models import AnsibleModuleLog
from rest_framework import serializers
from assets.models import *
from users.models import UserProfile
from django.contrib.auth.models import Permission, Group


class HostInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HostInfo
        fields = ('id', 'internal_ip', 'public_ip', 'system_ver', 'hostname',
                  'host_type', 'sn', 'manufacturer', 'server_model', 'mac', 'total_mem', 'cpu_counts',
                  'cpu_model', 'total_disk', 'scan_datetime')


class ModuleLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AnsibleModuleLog
        fields = ('id', 'ans_user', 'ans_remote_ip', 'ans_module', 'ans_args',
                  'ans_server', 'ans_result', 'ans_datetime')


class AssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Assets
        fields = (
            'id', 'asset_type', 'asset_nu', 'asset_provider', 'asset_status', 'asset_management_ip', 'asset_admin',
            'asset_project', 'asset_idc', 'asset_cabinets', 'asset_purchase_day', 'asset_expire_day', 'asset_price',
            'asset_memo')


class ServerAssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ServerAssets
        fields = (
            'id', 'asset', 'server_type', 'server_ip', 'username', 'auth_type', 'password', 'port',
            'hosted_on', 'hostname', 'cpu_model', 'cpu_number', 'vcpu_number', 'disk_total', 'ram_total', 'kernel',
            'system')


class NetworkAssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NetworkAssets
        fields = ('id', 'asset', 'network_type', 'port_number', 'firmware')


class OfficeAssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OfficeAssets
        fields = ('id', 'asset', 'office_type')


class SecurityAssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SecurityAssets
        fields = ('id', 'asset', 'security_type')


class StorageAssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageAssets
        fields = ('id', 'asset', 'storage_type')


class SoftwareAssetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SoftwareAssets
        fields = ('id', 'asset', 'software_type')


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'parent_project', 'project_name', 'project_memo')


class BusinessSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Business
        fields = ('id', 'project_name', 'business_name', 'business_memo')


class AssetProviderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AssetProvider
        fields = (
            'id', 'asset_provider_name', 'asset_provider_contact', 'asset_provider_telephone', 'asset_provider_memo')


class IDCSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IDC
        fields = ('id', 'idc_name', 'idc_address', 'idc_contact', 'idc_telephone', 'idc_memo')


class CabinetsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cabinets
        fields = ('id', 'idc', 'cabinets_name', 'cabinets_memo')


class UsersSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'password', 'mobile', 'is_superuser', 'is_active', 'groups', 'user_permissions')


class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')
