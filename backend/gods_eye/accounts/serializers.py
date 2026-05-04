from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password']
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data['user'] = user
        return data


class DeviceTokenSerializer(serializers.Serializer):
    """Register or replace the FCM device token for the authenticated user (companion app)."""

    fcm_device_token = serializers.CharField(
        allow_blank=True,
        max_length=4096,
        required=True,
    )
