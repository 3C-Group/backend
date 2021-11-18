from django.db import migrations


def init_data(apps, schema_editor):
    InstType = apps.get_model('appointment', 'InstrumentType')
    InstType.objects.create(name = "空", pk = 1)
    Inst = apps.get_model('appointment', 'Instrument')
    Inst.objects.create(name = "空", pk = 1, type = InstType.objects.get(pk = 1))
    Room = apps.get_model('appointment', 'Room')
    Room.objects.create(name = "空", pk = 1, max_inst = 114514)

class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(init_data),
    ]
