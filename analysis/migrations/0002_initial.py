# Generated by Django 3.2 on 2022-02-02 23:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('genomes', '0001_initial'),
        ('analysis', '0001_initial'),
        ('django_nextflow', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='gene',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='samples', to='genomes.gene'),
        ),
        migrations.AddField(
            model_name='sample',
            name='pi',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pi_submitted_samples', to='core.user'),
        ),
        migrations.AddField(
            model_name='sample',
            name='reads',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample', to='django_nextflow.data'),
        ),
        migrations.AddField(
            model_name='sample',
            name='scientist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_samples', to='core.user'),
        ),
        migrations.AddField(
            model_name='sample',
            name='species',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='samples', to='genomes.species'),
        ),
        migrations.AddField(
            model_name='sample',
            name='users',
            field=models.ManyToManyField(related_name='samples', through='analysis.SampleUserLink', to='core.User'),
        ),
        migrations.AddField(
            model_name='pipelinelink',
            name='pipeline',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='link', to='django_nextflow.pipeline'),
        ),
        migrations.AddField(
            model_name='paper',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='papers', to='analysis.collection'),
        ),
        migrations.AddField(
            model_name='jobuserlink',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.job'),
        ),
        migrations.AddField(
            model_name='jobuserlink',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user'),
        ),
        migrations.AddField(
            model_name='job',
            name='collection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='analysis.collection'),
        ),
        migrations.AddField(
            model_name='job',
            name='execution',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job', to='django_nextflow.execution'),
        ),
        migrations.AddField(
            model_name='job',
            name='pipeline',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='django_nextflow.pipeline'),
        ),
        migrations.AddField(
            model_name='job',
            name='sample',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='analysis.sample'),
        ),
        migrations.AddField(
            model_name='job',
            name='species',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='genomes.species'),
        ),
        migrations.AddField(
            model_name='job',
            name='users',
            field=models.ManyToManyField(related_name='jobs', through='analysis.JobUserLink', to='core.User'),
        ),
        migrations.AddField(
            model_name='datauserlink',
            name='data',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_nextflow.data'),
        ),
        migrations.AddField(
            model_name='datauserlink',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user'),
        ),
        migrations.AddField(
            model_name='datalink',
            name='collection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='analysis.collection'),
        ),
        migrations.AddField(
            model_name='datalink',
            name='data',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='link', to='django_nextflow.data'),
        ),
        migrations.AddField(
            model_name='collectionuserlink',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.collection'),
        ),
        migrations.AddField(
            model_name='collectionuserlink',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user'),
        ),
        migrations.AddField(
            model_name='collectiongrouplink',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.collection'),
        ),
        migrations.AddField(
            model_name='collectiongrouplink',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.group'),
        ),
        migrations.AddField(
            model_name='collection',
            name='groups',
            field=models.ManyToManyField(related_name='collections', through='analysis.CollectionGroupLink', to='core.Group'),
        ),
        migrations.AddField(
            model_name='collection',
            name='users',
            field=models.ManyToManyField(related_name='collections', through='analysis.CollectionUserLink', to='core.User'),
        ),
    ]
