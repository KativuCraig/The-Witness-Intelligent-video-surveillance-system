from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from alerts.models import Alert
from .serializers import AlertSerializer


class AlertViewSet(ReadOnlyModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(
            user=self.request.user
        ).select_related('incident').order_by('-sent_at')
