# Generated by Django 3.0.8 on 2020-12-23 00:56

from django.db import migrations, models

from visualizer.graphCreator.graphCreator import make_graph_with_file


def set_defaults_from_json(apps, schema_editor):
    """ Set the title and num candidates/rounds from the JSON file"""
    JsonConfig = apps.get_model('visualizer', 'JsonConfig')
    for jsonConfig in JsonConfig.objects.all().iterator():
        graph = make_graph_with_file(jsonConfig.jsonFile, False)
        jsonConfig.numRounds = len(graph.summarize().rounds)
        jsonConfig.numCandidates = len(graph.summarize().candidates)
        jsonConfig.title = graph.title
        jsonConfig.save()


def reverse_func(apps, schema_editor):
    """ Not needed: code to reverse the migration """


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0015_auto_20201217_0513'),
    ]

    operations = [
        # 1. Initialize with nullable fields
        migrations.AddField(
            model_name='jsonconfig',
            name='numCandidates',
            field=models.IntegerField(null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='jsonconfig',
            name='numRounds',
            field=models.IntegerField(null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='jsonconfig',
            name='title',
            field=models.CharField(null=True, max_length=256),
            preserve_default=False,
        ),

        # 2. Set all fields
        migrations.RunPython(set_defaults_from_json, reverse_func),

        # 3. Make them non-nullable
        migrations.AlterField(
            model_name='jsonconfig',
            name='numCandidates',
            field=models.IntegerField(null=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='jsonconfig',
            name='numRounds',
            field=models.IntegerField(null=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='jsonconfig',
            name='title',
            field=models.CharField(null=False, max_length=256),
            preserve_default=False,
        ),
    ]
