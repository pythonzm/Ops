from django.urls import path, include
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'inventory', views.InventoryViewSet)
router.register(r'assets', views.AssetsViewSet)
router.register(r'server_assets', views.ServerAssetsViewSet)
router.register(r'network_assets', views.NetworkAssetsViewSet)
router.register(r'office_assets', views.OfficeAssetsViewSet)
router.register(r'security_assets', views.SecurityAssetsViewSet)
router.register(r'storage_assets', views.StorageAssetsViewSet)
router.register(r'software_assets', views.SoftwareAssetsViewSet)
router.register(r'project', views.ProjectViewSet)
router.register(r'project_config', views.ProjectConfigViewSet)
router.register(r'service', views.ServiceViewSet)
router.register(r'asset_provider', views.AssetProviderViewSet)
router.register(r'idc', views.IDCViewSet)
router.register(r'cabinet', views.CabinetViewSet)
router.register(r'fort', views.FortViewSet)
router.register(r'fort_user', views.FortUserViewSet)
router.register(r'periodic_task', views.PeriodicTaskViewSet)
router.register(r'website', views.WebSiteViewSet)
router.register(r'post', views.PostViewSet)
router.register(r'pull_asset_conf', views.PullAssetConfViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'api/', include('rest_framework.urls', namespace='rest_framework'))
]
