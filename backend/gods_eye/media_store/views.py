from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from media_store.models import Evidence
from .serializers import EvidenceSerializer
from accounts.permissions import IsAdminOrSecurity


class EvidenceViewSet(ReadOnlyModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAdminOrSecurity]

    def get_queryset(self):
        incident_id = self.request.query_params.get('incident')
        qs = Evidence.objects.all()

        if incident_id:
            qs = qs.filter(incident_id=incident_id)

        return qs
