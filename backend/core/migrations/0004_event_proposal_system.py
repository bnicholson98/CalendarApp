# Generated migration for event proposal system

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0003_add_event_invite'),
    ]

    operations = [
        # Update Event model - add new fields
        migrations.AddField(
            model_name='event',
            name='status',
            field=models.CharField(
                choices=[('PROPOSED', 'Proposed'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled')],
                default='PROPOSED',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
            preserve_default=False,
        ),
        
        # Update Event user field to add related_name
        migrations.AlterField(
            model_name='event',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='events',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Update Event ordering
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['-created_at'], 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        
        # Remove the old date field from Event
        migrations.RemoveField(
            model_name='event',
            name='date',
        ),
        
        # Create ProposedDate model
        migrations.CreateModel(
            name='ProposedDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='proposed_dates',
                    to='core.event'
                )),
            ],
            options={
                'verbose_name': 'Proposed Date',
                'verbose_name_plural': 'Proposed Dates',
                'ordering': ['date'],
                'unique_together': {('event', 'date')},
            },
        ),
        
        # Add confirmed_date field to Event (after ProposedDate is created)
        migrations.AddField(
            model_name='event',
            name='confirmed_date',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='confirmed_events',
                to='core.proposeddate'
            ),
        ),
        
        # Create DateVote model
        migrations.CreateModel(
            name='DateVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('availability', models.CharField(
                    choices=[('AVAILABLE', 'Available'), ('MAYBE', 'Maybe'), ('NOT_AVAILABLE', 'Not Available')],
                    max_length=15
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proposed_date', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votes',
                    to='core.proposeddate'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='date_votes',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Date Vote',
                'verbose_name_plural': 'Date Votes',
                'ordering': ['-created_at'],
                'unique_together': {('proposed_date', 'user')},
            },
        ),
    ]
