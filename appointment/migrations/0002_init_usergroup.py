from django.db import migrations


def init_data(apps, schema_editor):
    UserGroup = apps.get_model('appointment', 'UserGroup')
    UserGroup.objects.create(name = "校内学生", pk = 1)
    UserGroup.objects.create(name = "校内老师", pk = 2)
    UserGroup.objects.create(name = "其他人士", pk = 3)

class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(init_data),
    ]
