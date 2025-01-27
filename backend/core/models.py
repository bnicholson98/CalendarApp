from django.db import models

class Event(models.Model):
    event_name = models.CharField(max_length=255)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    date = models.DateField()