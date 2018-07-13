from django.urls import path, include
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'hostinfo', views.HostInfoViewSet)
router.register(r'run_log', views.RunModuleLogViewSet)
router.register(r'assets', views.AssetsViewSet)
router.register(r'server_assets', views.ServerAssetsViewSet)
router.register(r'network_assets', views.NetworkAssetsViewSet)
router.register(r'office_assets', views.OfficeAssetsViewSet)
router.register(r'security_assets', views.SecurityAssetsViewSet)
router.register(r'storage_assets', views.StorageAssetsViewSet)
router.register(r'software_assets', views.SoftwareAssetsViewSet)
router.register(r'project', views.ProjectViewSet)
router.register(r'asset_provider', views.AssetProviderViewSet)
router.register(r'idc', views.IDCViewSet)
router.register(r'cabinets', views.CabinetsViewSet)
router.register(r'users', views.UsersViewSet)
router.register(r'permission', views.PermissionViewSet)
router.register(r'group', views.GroupViewSet)
router.register(r'user_log', views.UserLogViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'api/', include('rest_framework.urls', namespace='rest_framework'))
]
