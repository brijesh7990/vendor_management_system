from django.urls import path
from rest_framework.routers import DefaultRouter


from .views import *

router = DefaultRouter()
router.register(r"vendors", VendorViewSet)
router.register(r"purchase_orders", PurchaseOrderViewSet)
router.register(
    r"vendors/<int:vendor>/performance", PerformancemetricsView, basename="performance"
)

urlpatterns = router.urls
