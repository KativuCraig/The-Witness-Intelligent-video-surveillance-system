from django.urls import path
from .views import LoginView, DeviceTokenView

urlpatterns = [
    path('auth/login/', LoginView.as_view()),
    path('auth/device-token/', DeviceTokenView.as_view()),
]
