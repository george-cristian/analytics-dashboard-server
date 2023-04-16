from .models import CSVData
from rest_framework import serializers


class CSVDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVData
        fields = ('id', 'review_time', 'team', 'date', 'merge_time')
        