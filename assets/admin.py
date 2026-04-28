from django.contrib import admin
from django import forms
from assets.models import Assets, ServerAssets, NetworkAssets, OfficeAssets, SecurityAssets, StorageAssets, SoftwareAssets, DiskAssets, RamAssets, NetworkCardAssets, AssetProvider, IDC, Cabinet, AdminRecord, ZabbixAlert, WebSite, BusinessLine, PullAssetConf


class BusinessLineForm(forms.ModelForm):
    class Meta:
        model = BusinessLine
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            exclude_ids = [self.instance.pk] + [child.pk for child in self.instance.get_all_children()]
            self.fields['parent'].queryset = BusinessLine.objects.exclude(pk__in=exclude_ids)


class BusinessLineAdmin(admin.ModelAdmin):
    form = BusinessLineForm
    list_display = ('name', 'parent', 'level', 'sort', 'get_full_path', 'memo')
    list_filter = ('level', 'parent')
    search_fields = ('name', 'memo')
    ordering = ('sort', 'id')
    list_editable = ('sort',)

    def get_full_path(self, obj):
        return obj.get_full_path()
    get_full_path.short_description = '完整路径'

    def save_model(self, request, obj, form, change):
        if obj.parent:
            obj.level = obj.parent.level + 1
        else:
            obj.level = 1
        super().save_model(request, obj, form, change)


class AssetsAdmin(admin.ModelAdmin):
    list_display = ('asset_type', 'asset_nu', 'asset_model', 'asset_status', 'asset_management_ip',
                    'asset_admin', 'business_line_display', 'business_owner_display', 'asset_idc', 'asset_cabinet')
    list_filter = ('asset_type', 'asset_status', 'asset_admin', 'asset_idc', 'asset_business_line', 'asset_business_owner')
    search_fields = ('asset_nu', 'asset_model', 'asset_management_ip')
    readonly_fields = ('asset_create_time', 'asset_update_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('asset_type', 'asset_nu', 'asset_model', 'asset_status', 'asset_memo')
        }),
        ('业务信息', {
            'fields': ('asset_business_line', 'asset_business_owner')
        }),
        ('管理信息', {
            'fields': ('asset_admin', 'asset_management_ip')
        }),
        ('位置信息', {
            'fields': ('asset_provider', 'asset_idc', 'asset_cabinet')
        }),
        ('财务信息', {
            'fields': ('asset_purchase_day', 'asset_expire_day', 'asset_price')
        }),
        ('时间信息', {
            'fields': ('asset_create_time', 'asset_update_time'),
            'classes': ('collapse',)
        }),
    )

    def business_line_display(self, obj):
        if obj.asset_business_line:
            return obj.asset_business_line.get_full_path()
        return '-'
    business_line_display.short_description = '所属业务线'

    def business_owner_display(self, obj):
        if obj.asset_business_owner:
            return obj.asset_business_owner.username
        return '-'
    business_owner_display.short_description = '业务负责人'


class ServerAssetsAdmin(admin.ModelAdmin):
    list_display = ('assets', 'server_type', 'hostname', 'system', 'system_version', 'port')
    list_filter = ('server_type', 'system')
    search_fields = ('hostname', 'assets__asset_nu', 'assets__asset_management_ip')


class NetworkAssetsAdmin(admin.ModelAdmin):
    list_display = ('assets', 'network_type')
    list_filter = ('network_type',)
    search_fields = ('assets__asset_nu', 'assets__asset_management_ip')


class OfficeAssetsAdmin(admin.ModelAdmin):
    list_display = ('assets', 'office_type')
    list_filter = ('office_type',)
    search_fields = ('assets__asset_nu', 'assets__asset_management_ip')


class SecurityAssetsAdmin(admin.ModelAdmin):
    list_display = ('assets', 'security_type')
    list_filter = ('security_type',)
    search_fields = ('assets__asset_nu', 'assets__asset_management_ip')


class StorageAssetsAdmin(admin.ModelAdmin):
    list_display = ('assets', 'storage_type')
    list_filter = ('storage_type',)
    search_fields = ('assets__asset_nu', 'assets__asset_management_ip')


class SoftwareAssetsAdmin(admin.ModelAdmin):
    list_display = ('assets', 'software_type')
    list_filter = ('software_type',)
    search_fields = ('assets__asset_nu',)


class DiskAssetsAdmin(admin.ModelAdmin):
    list_display = ('asset', 'disk_slot', 'disk_volume', 'disk_model', 'disk_brand', 'disk_status')
    list_filter = ('disk_status', 'disk_brand')
    search_fields = ('asset__asset_nu', 'disk_serial', 'disk_model')


class RamAssetsAdmin(admin.ModelAdmin):
    list_display = ('asset', 'ram_slot', 'ram_volume', 'ram_brand', 'ram_serial')
    list_filter = ('ram_brand',)
    search_fields = ('asset__asset_nu', 'ram_serial')


class NetworkCardAssetsAdmin(admin.ModelAdmin):
    list_display = ('asset', 'network_card_name', 'network_card_mac', 'network_card_ip', 'network_card_status')
    list_filter = ('network_card_status',)
    search_fields = ('asset__asset_nu', 'network_card_mac', 'network_card_ip')


class AssetProviderAdmin(admin.ModelAdmin):
    list_display = ('asset_provider_name', 'asset_provider_contact', 'asset_provider_telephone', 'asset_provider_memo')
    search_fields = ('asset_provider_name', 'asset_provider_contact')


class IDCAdmin(admin.ModelAdmin):
    list_display = ('idc_name', 'idc_address', 'idc_contact', 'idc_telephone', 'idc_memo')
    search_fields = ('idc_name', 'idc_address')


class CabinetAdmin(admin.ModelAdmin):
    list_display = ('idc', 'cabinet_name', 'cabinet_memo')
    list_filter = ('idc',)
    search_fields = ('cabinet_name',)


class AdminRecordAdmin(admin.ModelAdmin):
    list_display = ('admin_login_user', 'admin_server', 'admin_remote_ip', 'admin_start_time',
                    'admin_login_status_time', 'admin_record_mode')
    list_filter = ('admin_record_mode', 'admin_login_user')
    search_fields = ('admin_server', 'admin_remote_ip')
    readonly_fields = ('admin_login_user', 'admin_server', 'admin_remote_ip', 'admin_start_time',
                       'admin_login_status_time', 'admin_record_mode', 'admin_record_file', 'admin_record_cmds')


class ZabbixAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_date', 'alert_num')
    list_filter = ('alert_date',)
    date_hierarchy = 'alert_date'


class WebSiteAdmin(admin.ModelAdmin):
    list_display = ('web_name', 'web_address', 'web_des')
    search_fields = ('web_name', 'web_address')


class PullAssetConfAdmin(admin.ModelAdmin):
    list_display = ('conf_name', 'cloud_name', 'cloud_region', 'belong_user', 'server_user', 'server_port')
    list_filter = ('cloud_name',)
    search_fields = ('conf_name', 'cloud_region')
    readonly_fields = ('access_key',)


admin.site.register(BusinessLine, BusinessLineAdmin)
admin.site.register(Assets, AssetsAdmin)
admin.site.register(ServerAssets, ServerAssetsAdmin)
admin.site.register(NetworkAssets, NetworkAssetsAdmin)
admin.site.register(OfficeAssets, OfficeAssetsAdmin)
admin.site.register(SecurityAssets, SecurityAssetsAdmin)
admin.site.register(StorageAssets, StorageAssetsAdmin)
admin.site.register(SoftwareAssets, SoftwareAssetsAdmin)
admin.site.register(DiskAssets, DiskAssetsAdmin)
admin.site.register(RamAssets, RamAssetsAdmin)
admin.site.register(NetworkCardAssets, NetworkCardAssetsAdmin)
admin.site.register(AssetProvider, AssetProviderAdmin)
admin.site.register(IDC, IDCAdmin)
admin.site.register(Cabinet, CabinetAdmin)
admin.site.register(AdminRecord, AdminRecordAdmin)
admin.site.register(ZabbixAlert, ZabbixAlertAdmin)
admin.site.register(WebSite, WebSiteAdmin)
admin.site.register(PullAssetConf, PullAssetConfAdmin)
