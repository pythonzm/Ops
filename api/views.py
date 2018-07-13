from rest_framework import viewsets, permissions
from api.serializers import *
from assets.models import *


class HostInfoViewSet(viewsets.ModelViewSet):
    """
    处理 /api/hostinfo/ GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = HostInfo.objects.all().order_by('id')
    serializer_class = HostInfoSerializer
    permission_classes = (permissions.IsAuthenticated,)


class RunModuleLogViewSet(viewsets.ModelViewSet):
    queryset = AnsibleModuleLog.objects.all().order_by('id')
    serializer_class = ModuleLogSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AssetsViewSet(viewsets.ModelViewSet):
    queryset = Assets.objects.all().order_by('id')
    serializer_class = AssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ServerAssetsViewSet(viewsets.ModelViewSet):
    queryset = ServerAssets.objects.all().order_by('id')
    serializer_class = ServerAssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class NetworkAssetsViewSet(viewsets.ModelViewSet):
    queryset = NetworkAssets.objects.all().order_by('id')
    serializer_class = NetworkAssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class OfficeAssetsViewSet(viewsets.ModelViewSet):
    queryset = OfficeAssets.objects.all().order_by('id')
    serializer_class = OfficeAssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class SecurityAssetsViewSet(viewsets.ModelViewSet):
    queryset = SecurityAssets.objects.all().order_by('id')
    serializer_class = SecurityAssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class StorageAssetsViewSet(viewsets.ModelViewSet):
    queryset = StorageAssets.objects.all().order_by('id')
    serializer_class = StorageAssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class SoftwareAssetsViewSet(viewsets.ModelViewSet):
    queryset = SoftwareAssets.objects.all().order_by('id')
    serializer_class = SoftwareAssetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated,)


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all().order_by('id')
    serializer_class = BusinessSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AssetProviderViewSet(viewsets.ModelViewSet):
    queryset = AssetProvider.objects.all().order_by('id')
    serializer_class = AssetProviderSerializer
    permission_classes = (permissions.IsAuthenticated,)


class IDCViewSet(viewsets.ModelViewSet):
    queryset = IDC.objects.all().order_by('id')
    serializer_class = IDCSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CabinetsViewSet(viewsets.ModelViewSet):
    queryset = Cabinets.objects.all().order_by('id')
    serializer_class = CabinetsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by('id')
    serializer_class = UsersSerializer
    permission_classes = (permissions.IsAuthenticated,)


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer
    permission_classes = (permissions.IsAuthenticated,)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UserLogViewSet(viewsets.ModelViewSet):
    queryset = UserLog.objects.all().order_by('id')
    serializer_class = UserLogSerializer
    permission_classes = (permissions.IsAuthenticated,)
