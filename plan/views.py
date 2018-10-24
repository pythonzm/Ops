from django.shortcuts import render
from django.http import JsonResponse
from django_celery_beat.models import CrontabSchedule, IntervalSchedule, PeriodicTask
from django_celery_results.models import TaskResult
from django.contrib.auth.decorators import permission_required
from plan.tasks import *


@permission_required('plan.add_periodictask', raise_exception=True)
def schedule_list(request):
    crontab_schedules = CrontabSchedule.objects.all()
    interval_schedules = IntervalSchedule.objects.all()
    timezone = app.conf.timezone
    return render(request, 'plan/schedule_list.html', locals())


def add_crontab_schedule(request):
    if request.method == 'POST':
        try:
            crontab_schedule = request.POST.dict()
            crontab_schedule_obj = CrontabSchedule.objects.create(**crontab_schedule)
            return JsonResponse({'code': 200, 'msg': '添加crontab_schedule成功', 'data': crontab_schedule_obj.id})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '添加crontab_schedule失败，{}'.format(e)})


def add_interval_schedule(request):
    if request.method == 'POST':
        try:
            interval_schedule = request.POST.dict()
            interval_schedule_obj = IntervalSchedule.objects.create(
                every=int(interval_schedule.get('every')),
                period=interval_schedule.get('period')
            )
            return JsonResponse({'code': 200, 'msg': '添加interval_schedule成功', 'data': interval_schedule_obj.id})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '添加interval_schedule失败，{}'.format(e)})


def del_schedule(request, pk):
    if request.method == 'POST':
        schedule_type = request.POST.get('schedule_type')
        if schedule_type == 'crontab_schedule':
            try:
                CrontabSchedule.objects.get(id=pk).delete()
                return JsonResponse({'code': 200, 'msg': '删除crontab_schedule成功'})
            except Exception as e:
                return JsonResponse({'code': 500, 'msg': '删除crontab_schedule失败，{}'.format(e)})
        elif schedule_type == 'interval_schedule':
            try:
                IntervalSchedule.objects.get(id=pk).delete()
                return JsonResponse({'code': 200, 'msg': '删除interval_schedule成功'})
            except Exception as e:
                return JsonResponse({'code': 500, 'msg': '删除interval_schedule失败，{}'.format(e)})


@permission_required('plan.add_periodictask', raise_exception=True)
def task_list(request):
    periodic_tasks = [periodic_task for periodic_task in PeriodicTask.objects.all() if
                      not periodic_task.task.startswith('celery.')]
    crontab_schedules = CrontabSchedule.objects.all()
    interval_schedules = IntervalSchedule.objects.all()
    celery_tasks = [task for task in app.tasks if task.startswith('plan.')]
    queues = [queue.name for queue in app.conf.task_queues]
    return render(request, 'plan/task_list.html', locals())


@permission_required('plan.add_taskresult', raise_exception=True)
def task_result(request):
    task_results = TaskResult.objects.all()
    return render(request, 'plan/task_result.html', locals())
