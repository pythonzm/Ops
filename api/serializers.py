# -*- coding: utf-8 -*-

from task.models import AnsibleInventory
from rest_framework import serializers
from assets.models import *
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


class PullAssetConfSerializer(serializers.ModelSerializer):
    class Meta:
        model = PullAssetConf
        fields = '__all__'

    def create(self, validated_data):
        validated_data['server_user_password'] = CryptPwd().encrypt_pwd(validated_data['server_user_password'])

        server = PullAssetConf.objects.create(**validated_data)
        return server

    def update(self, instance, validated_data):

        for attr, value in validated_data.items():
            if attr == 'server_user_password':
                if instance.server_user_password != value:
                    setattr(instance, attr, CryptPwd().encrypt_pwd(value))
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class ProjectConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectConfig
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
