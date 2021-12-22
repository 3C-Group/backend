from django.db import migrations


def init_data(apps, schema_editor):
    UserGroup = apps.get_model('appointment', 'UserGroup')
    UserGroup.objects.create(name = "校内学生", pk = 1)
    UserGroup.objects.create(name = "校内老师", pk = 2)
    UserGroup.objects.create(name = "其他人士", pk = 3)
    InstType = apps.get_model('appointment', 'InstrumentType')
    InstType.objects.create(name = "空乐器类型", pk = 1)
    Inst = apps.get_model('appointment', 'Instrument')
    Inst.objects.create(name = "不使用乐器", pk = 1, type = InstType.objects.get(pk = 1))
    Room = apps.get_model('appointment', 'Room')
    Room.objects.create(name = "不使用房间", pk = 1, max_inst = 114514)


def add_scheduled_task(apps, schema_editor):
    from django_q.models import Schedule
    Schedule.objects.create(
        func='appointment.tasks.expire_by_5min',
        minutes=1,
        repeats=-1,
    )
    Schedule.objects.create(
        func='appointment.tasks.expire_by_notused',
        minutes=1,
        repeats=-1,
    )

class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0001_initial'),
        ('django_q', '0014_schedule_cluster'),
    ]

    operations = [
        migrations.RunPython(init_data),
        migrations.RunPython(add_scheduled_task),
    ]
