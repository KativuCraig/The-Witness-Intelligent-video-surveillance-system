from rest_framework import serializers
from incidents.models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    video_source_name = serializers.CharField(
        source='video_source.name',
        read_only=True
    )

    class Meta:
        model = Incident
        fields = [
            'id',
            'incident_type',
            'confidence',
            'status',
            'detected_at',
            'created_at',
            'video_source',
            'video_source_name',
        ]
