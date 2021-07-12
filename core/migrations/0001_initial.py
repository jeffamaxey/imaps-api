# Generated by Django 2.2.20 on 2021-07-12 11:23

import core.models
from django.db import migrations, models
import django.db.models.deletion
import time


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('created', models.IntegerField(default=time.time)),
                ('last_modified', models.IntegerField(default=time.time)),
                ('description', models.TextField(blank=True, default='')),
                ('private', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'collections',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=200)),
                ('output_type', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'commands',
            },
        ),
        migrations.CreateModel(
            name='Execution',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=250)),
                ('created', models.IntegerField(default=time.time)),
                ('last_modified', models.IntegerField(default=time.time)),
                ('started', models.IntegerField(blank=True, null=True)),
                ('finished', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('warning', models.TextField(blank=True, null=True)),
                ('error', models.TextField(blank=True, null=True)),
                ('input', models.TextField(default='{}')),
                ('output', models.TextField(default='{}')),
                ('private', models.BooleanField(default=True)),
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='executions', to='core.Collection')),
                ('command', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='executions', to='core.Command')),
                ('demultiplex_execution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demultiplexed', to='core.Execution')),
                ('downstream', models.ManyToManyField(related_name='upstream', to='core.Execution')),
            ],
            options={
                'db_table': 'executions',
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True, validators=[core.models.slug_validator])),
                ('description', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'groups',
            },
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=250)),
                ('created', models.IntegerField(default=time.time)),
                ('last_modified', models.IntegerField(default=time.time)),
                ('private', models.BooleanField(default=True)),
                ('source', models.CharField(max_length=100)),
                ('organism', models.CharField(max_length=100)),
                ('qc_pass', models.NullBooleanField()),
                ('qc_message', models.CharField(max_length=100)),
                ('pi_name', models.CharField(max_length=100)),
                ('annotator_name', models.CharField(max_length=100)),
                ('collection', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='core.Collection')),
            ],
            options={
                'db_table': 'samples',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('username', models.SlugField(max_length=30, unique=True, validators=[core.models.slug_validator])),
                ('email', models.EmailField(max_length=200, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.IntegerField(default=None, null=True)),
                ('created', models.IntegerField(default=time.time)),
                ('name', models.CharField(max_length=50)),
                ('image', models.ImageField(default='', upload_to=core.models.create_filename)),
                ('password_reset_token', models.CharField(default='', max_length=128)),
                ('password_reset_token_expiry', models.IntegerField(default=0)),
                ('company', models.CharField(default='', max_length=100)),
                ('department', models.CharField(default='', max_length=100)),
                ('location', models.CharField(default='', max_length=100)),
                ('lab', models.CharField(default='', max_length=100)),
                ('job_title', models.CharField(default='', max_length=100)),
            ],
            options={
                'db_table': 'users',
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='UserGroupLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.IntegerField(choices=[[1, 'invited'], [2, 'member'], [3, 'admin']], default=1)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.User')),
            ],
            options={
                'db_table': 'user_group_links',
            },
        ),
        migrations.CreateModel(
            name='SampleUserLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.IntegerField(choices=[[1, 'access'], [2, 'edit'], [3, 'share']], default=1)),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Sample')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.User')),
            ],
            options={
                'db_table': 'sample_user_links',
            },
        ),
        migrations.AddField(
            model_name='sample',
            name='users',
            field=models.ManyToManyField(related_name='samples', through='core.SampleUserLink', to='core.User'),
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=250)),
                ('url', models.URLField(blank=True, null=True)),
                ('year', models.IntegerField()),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='papers', to='core.Collection')),
            ],
            options={
                'db_table': 'papers',
                'ordering': ['year'],
            },
        ),
        migrations.AddField(
            model_name='group',
            name='users',
            field=models.ManyToManyField(related_name='groups', through='core.UserGroupLink', to='core.User'),
        ),
        migrations.CreateModel(
            name='ExecutionUserLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.IntegerField(choices=[[1, 'access'], [2, 'edit'], [3, 'share'], [4, 'own']], default=1)),
                ('execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Execution')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.User')),
            ],
            options={
                'db_table': 'execution_user_links',
            },
        ),
        migrations.AddField(
            model_name='execution',
            name='initiator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='initiated_executions', to='core.User'),
        ),
        migrations.AddField(
            model_name='execution',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='core.Execution'),
        ),
        migrations.AddField(
            model_name='execution',
            name='sample',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='executions', to='core.Sample'),
        ),
        migrations.AddField(
            model_name='execution',
            name='users',
            field=models.ManyToManyField(related_name='executions', through='core.ExecutionUserLink', to='core.User'),
        ),
        migrations.CreateModel(
            name='CollectionUserLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.IntegerField(choices=[[1, 'access'], [2, 'edit'], [3, 'share'], [4, 'own']], default=1)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Collection')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.User')),
            ],
            options={
                'db_table': 'collection_user_links',
            },
        ),
        migrations.CreateModel(
            name='CollectionGroupLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.IntegerField(choices=[[1, 'access'], [2, 'edit'], [3, 'share']], default=1)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Collection')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Group')),
            ],
            options={
                'db_table': 'collection_group_links',
            },
        ),
        migrations.AddField(
            model_name='collection',
            name='groups',
            field=models.ManyToManyField(related_name='collections', through='core.CollectionGroupLink', to='core.Group'),
        ),
        migrations.AddField(
            model_name='collection',
            name='users',
            field=models.ManyToManyField(related_name='collections', through='core.CollectionUserLink', to='core.User'),
        ),
    ]
