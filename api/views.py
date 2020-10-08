import copy
from rest_framework import viewsets, permissions
from api.serializers import *


class CustomDjangoModelPermission(permissions.DjangoModelPermissions):

    def __init__(self):
        self.perms_map = copy.deepcopy(self.perms_map)  # you need deepcopy when you inherit a dictionary type
        self.perms_map['GET'] = ['%(app_label)s.add_%(model_name)s']


class InventoryViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = AnsibleInventory.objects.all().order_by('id')
    serializer_class = InventorySerializer
    permission_classes = (CustomDjangoModelPermission,)


class AssetsViewSet(viewsets.ModelViewSet):
    queryset = Assets.objects.all().order_by('id')
    serializer_class = AssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class ServerAssetsViewSet(viewsets.ModelViewSet):
    queryset = ServerAssets.objects.all().order_by('id')
    serializer_class = ServerAssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class NetworkAssetsViewSet(viewsets.ModelViewSet):
    queryset = NetworkAssets.objects.all().order_by('id')
    serializer_class = NetworkAssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class OfficeAssetsViewSet(viewsets.ModelViewSet):
    queryset = OfficeAssets.objects.all().order_by('id')
    serializer_class = OfficeAssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class SecurityAssetsViewSet(viewsets.ModelViewSet):
    queryset = SecurityAssets.objects.all().order_by('id')
    serializer_class = SecurityAssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class StorageAssetsViewSet(viewsets.ModelViewSet):
    queryset = StorageAssets.objects.all().order_by('id')
    serializer_class = StorageAssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class SoftwareAssetsViewSet(viewsets.ModelViewSet):
    queryset = SoftwareAssets.objects.all().order_by('id')
    serializer_class = SoftwareAssetsSerializer
    permission_classes = (CustomDjangoModelPermission,)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectSerializer
    permission_classes = (CustomDjangoModelPermission,)


class ProjectConfigViewSet(viewsets.ModelViewSet):
    queryset = ProjectConfig.objects.all().order_by('id')
    serializer_class = ProjectConfigSerializer
    permission_classes = (CustomDjangoModelPermission,)


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by('id')
    serializer_class = ServiceSerializer
    permission_classes = (CustomDjangoModelPermission,)


class AssetProviderViewSet(viewsets.ModelViewSet):
    queryset = AssetProvider.objects.all().order_by('id')
    serializer_class = AssetProviderSerializer
    permission_classes = (CustomDjangoModelPermission,)


class IDCViewSet(viewsets.ModelViewSet):
    queryset = IDC.objects.all().order_by('id')
    serializer_class = IDCSerializer
    permission_classes = (CustomDjangoModelPermission,)


class CabinetViewSet(viewsets.ModelViewSet):
    queryset = Cabinet.objects.all().order_by('id')
    serializer_class = CabinetSerializer
    permission_classes = (CustomDjangoModelPermission,)


class FortViewSet(viewsets.ModelViewSet):
    queryset = FortServer.objects.all().order_by('id')
    serializer_class = FortSerializer
    permission_classes = (CustomDjangoModelPermission,)


class FortUserViewSet(viewsets.ModelViewSet):
    queryset = FortServerUser.objects.all().order_by('id')
    serializer_class = FortUserSerializer
    permission_classes = (CustomDjangoModelPermission,)


class PeriodicTaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer
    permission_classes = (CustomDjangoModelPermission,)


class WebSiteViewSet(viewsets.ModelViewSet):
    queryset = WebSite.objects.all()
    serializer_class = WebSiteSerializer
    permission_classes = (CustomDjangoModelPermission,)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (CustomDjangoModelPermission,)

class PullAssetConfViewSet(viewsets.ModelViewSet):
    queryset = PullAssetConf.objects.all()
    serializer_class = PullAssetConfSerializer
    permission_classes = (CustomDjangoModelPermission,)