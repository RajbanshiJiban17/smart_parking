from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import UserProfile, Vehicle, ParkingArea, ParkingSlot, ParkingRate, Booking, ParkingRecord


class SmartParkingSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.driver_user = User.objects.create_user(
            username='testdriver',
            password='password123',
            email='testdriver@example.com',
            first_name='Test',
            last_name='Driver'
        )
        self.driver_profile = self.driver_user.profile
        self.driver_profile.role = 'CUSTOMER'
        self.driver_profile.phone_number = '9801234567'
        self.driver_profile.save()

        self.staff_user = User.objects.create_user(
            username='teststaff',
            password='password123',
            email='teststaff@example.com'
        )
        self.staff_profile = self.staff_user.profile
        self.staff_profile.role = 'STAFF'
        self.staff_profile.save()

        self.admin_user = User.objects.create_superuser(
            username='testadmin',
            password='password123',
            email='testadmin@example.com'
        )

        # Parking Rates
        self.rate_car = ParkingRate.objects.create(vehicle_type='CAR', hourly_rate=Decimal('50.00'))
        self.rate_bike = ParkingRate.objects.create(vehicle_type='MOTORCYCLE', hourly_rate=Decimal('20.00'))

        # Parking Area and Slots
        self.area = ParkingArea.objects.create(name='Main Lot', location='Zone 1', description='Central parking')
        self.slot1 = ParkingSlot.objects.create(parking_area=self.area, slot_number='P-01', vehicle_type='CAR', status='AVAILABLE')
        self.slot2 = ParkingSlot.objects.create(parking_area=self.area, slot_number='P-02', vehicle_type='CAR', status='AVAILABLE')

        # Vehicle
        self.vehicle = Vehicle.objects.create(
            user=self.driver_user,
            vehicle_number='BA-01-PA-9999',
            vehicle_type='CAR',
            vehicle_brand='Hyundai',
            vehicle_model='i20'
        )

    def test_user_profile_creation(self):
        """Verify UserProfile is automatically created via signals."""
        self.assertIsNotNone(self.driver_user.profile)
        self.assertEqual(self.driver_user.profile.role, 'CUSTOMER')

    def test_vehicle_creation_and_ownership(self):
        """Verify vehicle registration."""
        self.assertEqual(self.vehicle.user, self.driver_user)
        self.assertEqual(self.vehicle.vehicle_type, 'CAR')

    def test_booking_flow_status_transitions(self):
        """
        Verify booking flow:
        1. Slot is initially AVAILABLE.
        2. Booking is created -> slot status becomes RESERVED.
        3. Check-in -> slot status becomes OCCUPIED, booking becomes ACTIVE.
        4. Check-out -> slot status becomes AVAILABLE, booking becomes COMPLETED, fee calculated.
        """
        self.assertEqual(self.slot1.status, 'AVAILABLE')

        # 1. Create booking
        booking = Booking.objects.create(
            user=self.driver_user,
            vehicle=self.vehicle,
            parking_slot=self.slot1,
            booking_date=timezone.localdate(),
            expected_arrival_time=timezone.localtime().time(),
            status='RESERVED'
        )
        self.slot1.status = 'RESERVED'
        self.slot1.save()

        self.assertEqual(booking.status, 'RESERVED')
        self.assertTrue(booking.booking_reference.startswith('SP-'))
        self.assertEqual(self.slot1.status, 'RESERVED')

        # 2. Check-in (Vehicle Entry)
        entry_time = timezone.now() - timedelta(hours=1, minutes=15)
        record = ParkingRecord.objects.create(booking=booking, entry_time=entry_time)
        booking.status = 'ACTIVE'
        booking.save()
        self.slot1.status = 'OCCUPIED'
        self.slot1.save()

        self.assertEqual(booking.status, 'ACTIVE')
        self.assertEqual(self.slot1.status, 'OCCUPIED')

        # 3. Check-out (Vehicle Exit with Ceiling Fee calculation)
        exit_time = timezone.now()
        duration, fee = record.calculate_duration_and_fee(exit_time)
        record.save()
        booking.status = 'COMPLETED'
        booking.save()
        self.slot1.status = 'AVAILABLE'
        self.slot1.save()

        # 1 hour 15 minutes = 75 minutes = ceil(75/60) = 2 hours
        self.assertEqual(duration, 2)
        # 2 hours * Rs. 50 = Rs. 100.00
        self.assertEqual(fee, Decimal('100.00'))
        self.assertEqual(self.slot1.status, 'AVAILABLE')
        self.assertEqual(booking.status, 'COMPLETED')

    def test_booking_cancellation_frees_slot(self):
        """Cancelling a reservation must free the slot back to AVAILABLE."""
        booking = Booking.objects.create(
            user=self.driver_user,
            vehicle=self.vehicle,
            parking_slot=self.slot2,
            booking_date=timezone.localdate(),
            expected_arrival_time=timezone.localtime().time(),
            status='RESERVED'
        )
        self.slot2.status = 'RESERVED'
        self.slot2.save()

        # Perform cancellation
        self.client.login(username='testdriver', password='password123')
        response = self.client.post(reverse('booking_cancel', kwargs={'pk': booking.pk}))
        self.assertEqual(response.status_code, 302)

        booking.refresh_from_db()
        self.slot2.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(self.slot2.status, 'AVAILABLE')

    def test_role_based_access_control(self):
        """Ensure standard drivers cannot access Admin Dashboard."""
        self.client.login(username='testdriver', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

        # Staff can access check-in
        self.client.login(username='teststaff', password='password123')
        response = self.client.get(reverse('staff_check_in'))
        self.assertEqual(response.status_code, 200)

        # Admin can access admin dashboard
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
