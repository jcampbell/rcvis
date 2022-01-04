# Generated by Django 3.2.5 on 2022-01-03 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0027_alter_jsonconfig_textforwinner'),
        ('accounts', '0002_userprofile_downloadedrawdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='downloadedRawData',
            field=models.ManyToManyField(
                blank=True,
                related_name='rawDownloadedBy',
                to='visualizer.JsonConfig'),
        ),
    ]
