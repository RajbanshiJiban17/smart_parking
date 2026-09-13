import uuid
import math
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile for role-based access and phone number.
    Roles:
      - ADMIN: Administrator with full access to manage areas, slots, rates, reports, users.
      - STAFF: Parking staff who can check-in and check-out vehicles.
      - CUSTOMER: Standard registered vehicle owner/driver.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('STAFF', 'Parking Staff'),
        ('CUSTOMER', 'Customer / Driver'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')

    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser

    def is_staff_member(self):
        return self.role in ['ADMIN', 'STAFF'] or self.user.is_staff or self.user.is_superuser

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure every User has an associated UserProfile."""
    if created:
        role = 'ADMIN' if instance.is_superuser else 'CUSTOMER'
        UserProfile.objects.create(user=instance, role=role)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            role = 'ADMIN' if instance.is_superuser else 'CUSTOMER'
            UserProfile.objects.create(user=instance, role=role)


class Vehicle(models.Model):
    """
    Vehicle owned by a registered user.
    """
    VEHICLE_TYPES = [
        ('CAR', 'Car'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('BICYCLE', 'Bicycle'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_number = models.CharField(max_length=50, unique=True, help_text="e.g., BA-02-PA-1234 or DL-01-AB-1234")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='CAR')
    vehicle_brand = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle_number} - {self.vehicle_brand} {self.vehicle_model} ({self.get_vehicle_type_display()})"


class ParkingArea(models.Model):
    """
    Parking area or zone (e.g., Main Parking, College Premises, Visitor Parking).
    """
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.location})"

    @property
    def total_slots(self):
        return self.slots.count()

    @property
    def available_slots_count(self):
        return self.slots.filter(status='AVAILABLE').count()

    @property
    def occupied_slots_count(self):
        return self.slots.filter(status='OCCUPIED').count()

    @property
    def reserved_slots_count(self):
        return self.slots.filter(status='RESERVED').count()


class ParkingSlot(models.Model):
    """
    Individual parking slot within a parking area.
    """
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('RESERVED', 'Reserved'),
    ]

    parking_area = models.ForeignKey(ParkingArea, on_delete=models.CASCADE, related_name='slots')
    slot_number = models.CharField(max_length=20, help_text="e.g., A-01, B-02")
    vehicle_type = models.CharField(max_length=20, choices=Vehicle.VEHICLE_TYPES, default='CAR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    class Meta:
        ordering = ['parking_area', 'slot_number']
        unique_together = ('parking_area', 'slot_number')

    def __str__(self):
        return f"{self.parking_area.name} - Slot {self.slot_number} [{self.get_vehicle_type_display()}] ({self.get_status_display()})"


class ParkingRate(models.Model):
    """
    Parking fee rates per hour per vehicle type.
    """
    vehicle_type = models.CharField(max_length=20, choices=Vehicle.VEHICLE_TYPES, unique=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, help_text="Hourly rate in standard currency")

    class Meta:
        ordering = ['vehicle_type']

    def __str__(self):
        return f"{self.get_vehicle_type_display()}: Rs. {self.hourly_rate}/hour"


class Booking(models.Model):
    """
    Reservation record for a parking slot by a user for their vehicle.
    """
    STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking_reference = models.CharField(max_length=40, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    parking_slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    expected_arrival_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RESERVED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            year = timezone.now().strftime("%Y")
            random_part = uuid.uuid4().hex[:6].upper()
            self.booking_reference = f"SP-{year}-{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.booking_reference}] {self.user.username} - {self.vehicle.vehicle_number} ({self.get_status_display()})"


class ParkingRecord(models.Model):
    """
    Check-in and check-out record tracking parking duration and calculated fee.
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='record')
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Total billable hours rounded up via ceiling logic")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-entry_time']

    def calculate_duration_and_fee(self, exit_dt=None):
        """
        Calculates parking duration and total fee using ceiling rule:
        Partial hours rounded up via math.ceil.
        Duration = ceil((exit_time - entry_time) in seconds / 3600)
        Minimum duration is 1 hour.
        """
        if exit_dt is None:
            exit_dt = timezone.now()
        self.exit_time = exit_dt

        # Calculate time difference
        delta = self.exit_time - self.entry_time
        total_seconds = max(0, delta.total_seconds())

        # math.ceil to round up any partial hour, with a minimum of 1 hour
        calculated_hours = math.ceil(total_seconds / 3600)
        self.duration = max(1, calculated_hours)

        # Lookup rate for vehicle type
        vehicle_type = self.booking.vehicle.vehicle_type
        rate_obj = ParkingRate.objects.filter(vehicle_type=vehicle_type).first()
        if rate_obj:
            hourly = rate_obj.hourly_rate
        else:
            # Fallback default rate if not defined
            defaults = {'CAR': Decimal('50.00'), 'MOTORCYCLE': Decimal('20.00'), 'BICYCLE': Decimal('10.00'), 'OTHER': Decimal('30.00')}
            hourly = defaults.get(vehicle_type, Decimal('30.00'))

        self.total_fee = Decimal(self.duration) * Decimal(str(hourly))
        return self.duration, self.total_fee

    def __str__(self):
        return f"Record for {self.booking.booking_reference} - Entry: {self.entry_time.strftime('%Y-%m-%d %H:%M')}"
