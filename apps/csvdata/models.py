from django.db import models
from django.contrib.auth.models import User

class CSVData(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    review_time = models.CharField(max_length=100)
    team        = models.CharField(max_length=100)
    date        = models.DateField()
    merge_time  = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'CSV Data'

    def __str__(self) -> str:
        return f'{self.review_time} - {self.team} - {self.date} - {self.merge_time}'
