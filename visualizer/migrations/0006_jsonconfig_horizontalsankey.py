# Generated by Django 2.2.3 on 2019-10-24 00:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('visualizer', '0005_auto_20191016_0019'),
    ]

    operations = [
        migrations.AddField(
            model_name='jsonconfig',
            name='horizontalSankey',
            field=models.BooleanField(default=False),
        ),
    ]
