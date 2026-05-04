from rest_framework import serializers
from cameras.models import VideoSource


class VideoSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSource
        fields = '__all__'
