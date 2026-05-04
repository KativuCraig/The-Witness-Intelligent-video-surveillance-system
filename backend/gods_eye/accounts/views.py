from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from .serializers import LoginSerializer, DeviceTokenSerializer


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
            }
        }, status=status.HTTP_200_OK)


class DeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data.get("fcm_device_token", "")
        request.user.fcm_device_token = token.strip()
        request.user.save(update_fields=["fcm_device_token"])
        return Response({"detail": "Device token saved."}, status=status.HTTP_200_OK)

    def delete(self, request):
        request.user.fcm_device_token = ""
        request.user.save(update_fields=["fcm_device_token"])
        return Response({"detail": "Device token cleared."}, status=status.HTTP_200_OK)
