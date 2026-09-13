from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from parking.models import UserProfile, Vehicle, ParkingArea, ParkingSlot, ParkingRate, Booking, ParkingRecord


class Command(BaseCommand):
    help = "Seed database with initial demo users, parking areas, slots, rates, and sample bookings."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Smart Parking database with sample data..."))

        # 1. Create Users
        # Admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartparking.edu',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        admin_profile.role = 'ADMIN'
        admin_profile.phone_number = '9800000001'
        admin_profile.save()

        # Staff
        staff_user, created = User.objects.get_or_create(
            username='staff',
            defaults={
                'email': 'staff@smartparking.edu',
                'first_name': 'Parking',
                'last_name': 'Attendant',
                'is_staff': True,
            }
        )
        staff_user.set_password('staff123')
        staff_user.save()
        staff_profile, _ = UserProfile.objects.get_or_create(user=staff_user)
        staff_profile.role = 'STAFF'
        staff_profile.phone_number = '9800000002'
        staff_profile.save()

        # Driver
        driver_user, created = User.objects.get_or_create(
            username='driver',
            defaults={
                'email': 'driver@smartparking.edu',
                'first_name': 'Suman',
                'last_name': 'Sharma',
            }
        )
        driver_user.set_password('driver123')
        driver_user.save()
        driver_profile, _ = UserProfile.objects.get_or_create(user=driver_user)
        driver_profile.role = 'CUSTOMER'
        driver_profile.phone_number = '9841234567'
        driver_profile.save()

        self.stdout.write(self.style.SUCCESS("[OK] Users created (admin/admin123, staff/staff123, driver/driver123)"))

        # 2. Hourly Parking Rates (Section 16 & 37)
        rates_data = [
            ('CAR', Decimal('50.00')),
            ('MOTORCYCLE', Decimal('20.00')),
            ('BICYCLE', Decimal('10.00')),
            ('OTHER', Decimal('40.00')),
        ]
        for vtype, hourly in rates_data:
            ParkingRate.objects.update_or_create(
                vehicle_type=vtype,
                defaults={'hourly_rate': hourly}
            )
        self.stdout.write(self.style.SUCCESS("[OK] Parking rates initialized (Car: Rs. 50/hr, Motorcycle: Rs. 20/hr, Bicycle: Rs. 10/hr)"))

        # 3. Parking Areas (Section 8 & 37)
        areas_data = [
            {
                'name': 'Main Parking Area',
                'location': 'Central Campus Gate 1',
                'description': 'Main parking facility for students, staff, and campus visitors.'
            },
            {
                'name': 'College Premises Parking',
                'location': 'Academic Block B Courtyard',
                'description': 'Dedicated bays for everyday two-wheelers and staff automobiles.'
            },
            {
                'name': 'Visitor Parking Area',
                'location': 'North Entry Perimeter',
                'description': 'Short-term guest vehicle parking.'
            },
        ]

        created_areas = []
        for a_data in areas_data:
            area, _ = ParkingArea.objects.update_or_create(
                name=a_data['name'],
                defaults={'location': a_data['location'], 'description': a_data['description']}
            )
            created_areas.append(area)
        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(created_areas)} parking areas"))

        # 4. Parking Slots (Section 9 & 37)
        slot_plan = [
            # Main Parking Area (Area 0)
            (created_areas[0], 'A-01', 'CAR', 'AVAILABLE'),
            (created_areas[0], 'A-02', 'CAR', 'AVAILABLE'),
            (created_areas[0], 'A-03', 'CAR', 'AVAILABLE'),
            (created_areas[0], 'A-04', 'CAR', 'AVAILABLE'),
            (created_areas[0], 'A-05', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[0], 'A-06', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[0], 'A-07', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[0], 'A-08', 'BICYCLE', 'AVAILABLE'),

            # College Premises Parking (Area 1)
            (created_areas[1], 'B-01', 'CAR', 'AVAILABLE'),
            (created_areas[1], 'B-02', 'CAR', 'AVAILABLE'),
            (created_areas[1], 'B-03', 'CAR', 'AVAILABLE'),
            (created_areas[1], 'B-04', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[1], 'B-05', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[1], 'B-06', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[1], 'B-07', 'BICYCLE', 'AVAILABLE'),
            (created_areas[1], 'B-08', 'OTHER', 'AVAILABLE'),

            # Visitor Parking Area (Area 2)
            (created_areas[2], 'C-01', 'CAR', 'AVAILABLE'),
            (created_areas[2], 'C-02', 'CAR', 'AVAILABLE'),
            (created_areas[2], 'C-03', 'CAR', 'AVAILABLE'),
            (created_areas[2], 'C-04', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[2], 'C-05', 'MOTORCYCLE', 'AVAILABLE'),
            (created_areas[2], 'C-06', 'BICYCLE', 'AVAILABLE'),
        ]

        created_slots = {}
        for area, slot_num, vtype, status in slot_plan:
            slot, _ = ParkingSlot.objects.update_or_create(
                parking_area=area,
                slot_number=slot_num,
                defaults={'vehicle_type': vtype, 'status': status}
            )
            created_slots[slot_num] = slot
        self.stdout.write(self.style.SUCCESS(f"[OK] Configured {len(slot_plan)} parking slots across all areas"))

        # 5. Sample Vehicles for Driver
        v1, _ = Vehicle.objects.update_or_create(
            vehicle_number='BA-02-PA-1234',
            defaults={
                'user': driver_user,
                'vehicle_type': 'CAR',
                'vehicle_brand': 'Toyota',
                'vehicle_model': 'Corolla',
            }
        )
        v2, _ = Vehicle.objects.update_or_create(
            vehicle_number='BA-03-PA-9876',
            defaults={
                'user': driver_user,
                'vehicle_type': 'MOTORCYCLE',
                'vehicle_brand': 'Yamaha',
                'vehicle_model': 'FZ-S',
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Driver vehicles registered"))

        # 6. Sample Booking 1: ACTIVE (Occupied slot A-02)
        slot_a2 = created_slots['A-02']
        b1, _ = Booking.objects.update_or_create(
            booking_reference='SP-2026-DEMO01',
            defaults={
                'user': driver_user,
                'vehicle': v1,
                'parking_slot': slot_a2,
                'booking_date': timezone.localdate(),
                'expected_arrival_time': (timezone.localtime() - timedelta(hours=2)).time(),
                'status': 'ACTIVE',
            }
        )
        slot_a2.status = 'OCCUPIED'
        slot_a2.save()

        rec1, _ = ParkingRecord.objects.update_or_create(
            booking=b1,
            defaults={
                'entry_time': timezone.now() - timedelta(hours=2, minutes=15),
            }
        )

        # Sample Booking 2: RESERVED (Reserved slot A-03)
        slot_a3 = created_slots['A-03']
        b2, _ = Booking.objects.update_or_create(
            booking_reference='SP-2026-DEMO02',
            defaults={
                'user': driver_user,
                'vehicle': v2,
                'parking_slot': slot_a3,
                'booking_date': timezone.localdate(),
                'expected_arrival_time': (timezone.localtime() + timedelta(hours=1)).time(),
                'status': 'RESERVED',
            }
        )
        slot_a3.status = 'RESERVED'
        slot_a3.save()

        # Sample Booking 3: COMPLETED history record (Slot A-01 freed)
        slot_a1 = created_slots['A-01']
        b3, _ = Booking.objects.update_or_create(
            booking_reference='SP-2026-DEMO03',
            defaults={
                'user': driver_user,
                'vehicle': v1,
                'parking_slot': slot_a1,
                'booking_date': timezone.localdate() - timedelta(days=1),
                'expected_arrival_time': timezone.localtime().time(),
                'status': 'COMPLETED',
            }
        )
        entry_dt = timezone.now() - timedelta(days=1, hours=4)
        exit_dt = timezone.now() - timedelta(days=1, hours=1)
        rec3, _ = ParkingRecord.objects.update_or_create(
            booking=b3,
            defaults={
                'entry_time': entry_dt,
                'exit_time': exit_dt,
                'duration': 3,
                'total_fee': Decimal('150.00'),
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Initialized demo booking scenarios (Occupied, Reserved, and Completed)"))
        self.stdout.write(self.style.SUCCESS("[DONE] Database seeding complete! Ready for presentation and testing."))
