from django.db import models
from django.db.models import F, Avg
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import uuid
from django.utils.timezone import now


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    contact_details = models.TextField()
    address = models.TextField()
    vendor_code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    on_time_delivery_rate = models.FloatField(default=0)
    quality_rating_avg = models.FloatField(default=0)
    average_response_time = models.FloatField(default=0)
    fulfillment_rate = models.FloatField(default=0)

    def __str__(self):
        return str(self.id)


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]

    po_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField()
    items = models.JSONField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    quality_rating = models.FloatField(null=True, blank=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    acknowledgment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == "completed":
            self.update_vendor_performance()
        self.update_average_response_time(self.vendor)
        self.update_fulfillment_rate(self.vendor)
        self.create_historical_performance()

    def update_vendor_performance(self):
        completed_orders = PurchaseOrder.objects.filter(
            vendor=self.vendor, status="completed"
        )
        on_time_orders = completed_orders.filter(delivery_date__lte=F("delivery_date"))

        if completed_orders.exists():
            self.vendor.on_time_delivery_rate = (
                on_time_orders.count() / completed_orders.count() * 100
            )
        else:
            self.vendor.on_time_delivery_rate = 0

        quality_rating = PurchaseOrder.objects.filter(
            vendor=self.vendor, status="completed"
        ).aggregate(Avg("quality_rating"))["quality_rating__avg"]
        self.vendor.quality_rating_avg = quality_rating if quality_rating else 0
        self.vendor.save()

    def update_average_response_time(self, vendor):
        acknowledged_pos = PurchaseOrder.objects.filter(
            vendor=vendor, acknowledgment_date__isnull=False
        )
        if not acknowledged_pos.exists():
            vendor.average_response_time = 0
            vendor.save()
            return

        total_response_time = 0
        for po in acknowledged_pos:
            response_time = (po.acknowledgment_date - po.issue_date).total_seconds()
            total_response_time += response_time

        vendor.average_response_time = total_response_time / acknowledged_pos.count()
        vendor.save()

    def update_fulfillment_rate(self, vendor):
        total_pos = PurchaseOrder.objects.filter(vendor=vendor).count()
        if total_pos == 0:
            vendor.fulfillment_rate = 0
            vendor.save()
            return

        completed_pos = PurchaseOrder.objects.filter(
            vendor=vendor, status="completed"
        ).count()
        vendor.fulfillment_rate = completed_pos / total_pos * 100
        vendor.save()

    def create_historical_performance(self):
        HistoricalPerformance.objects.create(
            vendor=self.vendor,
            date=now(),
            on_time_delivery_rate=self.vendor.on_time_delivery_rate,
            quality_rating_avg=self.vendor.quality_rating_avg,
            average_response_time=self.vendor.average_response_time,
            fulfillment_rate=self.vendor.fulfillment_rate,
        )


class HistoricalPerformance(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()

    def __str__(self):
        return f"{self.vendor.name} - {self.date}"
