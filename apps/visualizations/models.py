from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

class Visualization(models.Model):
    user               = models.ForeignKey(User, on_delete=models.CASCADE)
    visualization_type = models.CharField(max_length=50)
    file_path          = models.CharField(max_length=255)
    created_at         = models.DateTimeField(auto_now_add=True)
    teams              = ArrayField(models.CharField(max_length=50), blank=True)
    shared_with        = models.ManyToManyField(User, related_name='shared_visualizations', blank=True)
