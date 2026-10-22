from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ItemGroupViewSet, ItemViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("groups", ItemGroupViewSet, basename="item-group")
router.register("items", ItemViewSet, basename="item")

urlpatterns = router.urls
