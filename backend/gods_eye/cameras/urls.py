from rest_framework.routers import DefaultRouter
from .views import VideoSourceViewSet

router = DefaultRouter()
router.register(r'cameras', VideoSourceViewSet)

urlpatterns = router.urls
