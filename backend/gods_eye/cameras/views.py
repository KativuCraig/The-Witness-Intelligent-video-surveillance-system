from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from cameras.models import VideoSource
from .serializers import VideoSourceSerializer
from accounts.permissions import IsAdmin


class VideoSourceViewSet(ModelViewSet):
    queryset = VideoSource.objects.all()
    serializer_class = VideoSourceSerializer
    permission_classes = [IsAdmin]


