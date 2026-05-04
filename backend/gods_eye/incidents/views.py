from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from incidents.models import Incident
from .serializers import IncidentSerializer


class IsAdminOrSecurity(BasePermission):
    """
    Permission to only allow ADMIN and SECURITY roles to access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['ADMIN', 'SECURITY']


class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Incident.objects.all().order_by('-created_at')
    serializer_class = IncidentSerializer
    permission_classes = [IsAdminOrSecurity]

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Security operator confirms the alert (incident is real / being handled).
        Sets status to ACKNOWLEDGED when currently NEW.
        """
        incident = self.get_object()
        if incident.status == 'RESOLVED':
            return Response(
                {'detail': 'This incident is already dismissed (resolved).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if incident.status == 'NEW':
            incident.status = 'ACKNOWLEDGED'
            incident.save(update_fields=['status'])
        data = IncidentSerializer(incident).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss(self, request, pk=None):
        """
        Operator dismisses the alert (e.g. false alarm or no further action).
        Sets status to RESOLVED.
        """
        incident = self.get_object()
        if incident.status != 'RESOLVED':
            incident.status = 'RESOLVED'
            incident.save(update_fields=['status'])
        data = IncidentSerializer(incident).data
        return Response(data, status=status.HTTP_200_OK)
