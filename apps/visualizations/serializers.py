from rest_framework import serializers
from .models import Visualization

class VisualizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visualization
        fields = ['id', 'user', 'visualization_type', 'file_path', 'created_at', 'teams']
