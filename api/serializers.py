# -*- coding: utf-8 -*-

from task.models import AnsibleInventory
from rest_framework import serializers
from assets.models import *
from users.models import UserProfile, UserLog
from django.contrib.auth.models import Permission, Group
from utils.crypt_pwd import CryptPwd
from fort.models import *
from projs.models import *
from django_celery_beat.models import PeriodicTask
from wiki.models import Post


class AssetsSerializer(serializers.ModelSerializer):
    asset_management_ip = serializers.IPAddressField(allow_blank=True, allow_null=True)

    class Meta:
        model = Assets
        fields = '__all__'


class ServerAssetsSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=False, required=False)

    class Meta:
        model = ServerAssets
        fields = '__all__'

    def create(self, data):
        if data.get('assets'):
            assets_data = data.pop('assets')
            assets = Assets.objects.create(**assets_data)
        else:
            assets = Assets()
        data['assets'] = assets
        data['password'] = CryptPwd().encrypt_pwd(data['password'])
        server = ServerAssets.objects.create(**data)
        return server


class NetworkAssetsSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=False, required=False)

    class Meta:
        model = NetworkAssets
        fields = '__all__'

    def create(self, data):
        if data.get('assets'):
            assets_data = data.pop('assets')
            assets = Assets.objects.create(**assets_data)
        else:
            assets = Assets()
        data['assets'] = assets
        network = NetworkAssets.objects.create(**data)
        return network


class OfficeAssetsSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=False, required=False)

    class Meta:
        model = OfficeAssets
        fields = '__all__'

    def create(self, data):
        if data.get('assets'):
            assets_data = data.pop('assets')
            assets = Assets.objects.create(**assets_data)
        else:
            assets = Assets()
        data['assets'] = assets
        office = OfficeAssets.objects.create(**data)
        return office


class SecurityAssetsSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=False, required=False)

    class Meta:
        model = SecurityAssets
        fields = '__all__'

    def create(self, data):
        if data.get('assets'):
            assets_data = data.pop('assets')
            assets = Assets.objects.create(**assets_data)
        else:
            assets = Assets()
        data['assets'] = assets
        security = SecurityAssets.objects.create(**data)
        return security


class StorageAssetsSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=False, required=False)

    class Meta:
        model = StorageAssets
        fields = '__all__'

    def create(self, data):
        if data.get('assets'):
            assets_data = data.pop('assets')
            assets = Assets.objects.create(**assets_data)
        else:
            assets = Assets()
        data['assets'] = assets
        storage = StorageAssets.objects.create(**data)
        return storage


class SoftwareAssetsSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=False, required=False)

    class Meta:
        model = SoftwareAssets
        fields = '__all__'

    def create(self, data):
        if data.get('assets'):
            assets_data = data.pop('assets')
            assets = Assets.objects.create(**assets_data)
        else:
            assets = Assets()
        data['assets'] = assets
        software = StorageAssets.objects.create(**data)
        return software


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class AssetProviderSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=True, read_only=True)

    class Meta:
        model = AssetProvider
        fields = (
            'id', 'asset_provider_name', 'asset_provider_contact', 'asset_provider_telephone', 'asset_provider_memo',
            'assets')


class CabinetSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=True, read_only=True)

    class Meta:
        model = Cabinet
        fields = ('id', 'idc', 'cabinet_name', 'cabinet_memo', 'assets')


class IDCSerializer(serializers.ModelSerializer):
    cabinet = CabinetSerializer(many=True, read_only=True)
    assets = AssetsSerializer(many=True, read_only=True)

    class Meta:
        model = IDC
        fields = ('id', 'idc_name', 'idc_address', 'idc_contact', 'idc_telephone', 'idc_memo', 'cabinet', 'assets')


class UsersSerializer(serializers.ModelSerializer):
    assets = AssetsSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'mobile', 'is_superuser', 'is_active', 'groups', 'user_permissions', 'assets')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name')


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'user_set', 'permissions')


class UserLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLog
        fields = '__all__'


class AssetsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetsLog
        fields = '__all__'


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AnsibleInventory
        fields = '__all__'


class FortSerializer(serializers.ModelSerializer):
    class Meta:
        model = FortServer
        fields = '__all__'


class FortUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FortServerUser
        fields = '__all__'


class PeriodicTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'


class WebSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebSite
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
