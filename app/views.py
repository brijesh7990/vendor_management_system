from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import *
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

# Create your views here.


from rest_framework import viewsets
from .models import Vendor, PurchaseOrder
from .serializers import VendorSerializer, PurchaseOrderSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def performance(self, request, pk=None):
        vendor = self.get_object()
        performance_data = {
            "on_time_delivery_rate": vendor.on_time_delivery_rate,
            "quality_rating_avg": vendor.quality_rating_avg,
            "average_response_time": vendor.average_response_time,
            "fulfillment_rate": vendor.fulfillment_rate,
        }
        return Response(performance_data)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        vendor_id = self.request.query_params.get("vendor", None)
        if vendor_id:
            return self.queryset.filter(vendor__id=vendor_id)
        return self.queryset


class PerformancemetricsView(viewsets.ViewSet):
    serializer_class = Performancemetricsserializer
    permission_classes = [IsAuthenticated]

    def get(self, request, vendor=None):
        try:
            data = Vendor.objects.values(
                "on_time_delivery_rate",
                "quality_rating_avg",
                "average_response_time",
                "fulfillment_rate",
            ).filter(id=int(vendor))

            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                return Response(serializer.data)
        except Vendor.DoesNotExist:
            return Response({"message": "Vendor not found"}, status=404)
