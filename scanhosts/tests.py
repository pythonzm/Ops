from django.apps import apps

obj = apps.get_model('scanhosts', 'HostInfo')
print(obj)
