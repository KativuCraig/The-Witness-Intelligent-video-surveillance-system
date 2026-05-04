from rest_framework import serializers
from alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    incident_type = serializers.CharField(
        source='incident.incident_type',
        read_only=True
    )
    incident_status = serializers.CharField(
        source='incident.status',
        read_only=True
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'incident',
            'incident_type',
            'incident_status',
            'sent_at',
            'delivery_status',
        ]
