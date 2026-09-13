import math
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator

from .models import (
    UserProfile,
    Vehicle,
    ParkingArea,
    ParkingSlot,
    ParkingRate,
    Booking,
    ParkingRecord,
)
from .forms import (
    UserRegistrationForm,
    UserProfileForm,
    VehicleForm,
    ParkingAreaForm,
    ParkingSlotForm,
    ParkingRateForm,
    BookingForm,
    StaffSearchForm,
    ReportFilterForm,
)


# ==========================================
# ACCESS CONTROL HELPERS
# ==========================================

def is_admin_check(user):
    """Check if user has Administrator privileges."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'


def is_staff_or_admin_check(user):
    """Check if user has Staff or Administrator privileges."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'STAFF']


def admin_required(view_func):
    """Decorator to restrict view to Admins only."""
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_check(request.user):
            messages.error(request, "Access denied. You do not have administrator permissions.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_admin_required(view_func):
    """Decorator to restrict view to Staff and Admins."""
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not is_staff_or_admin_check(request.user):
            messages.error(request, "Access denied. You do not have staff/admin permissions.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def register_view(request):
    """Register a new customer account."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Ensure profile has phone number and customer role
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = form.cleaned_data['phone_number']
            profile.role = 'CUSTOMER'
            profile.save()

            messages.success(request, f"Welcome, {user.first_name or user.username}! Your account was created successfully.")
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User login supporting redirects based on user role."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")

            # Smart redirect based on role
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if is_admin_check(user):
                return redirect('admin_dashboard')
            elif hasattr(user, 'profile') and user.profile.role == 'STAFF':
                return redirect('staff_check_in')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """User logout."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def profile_view(request):
    """View and update profile information."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        phone = request.POST.get('phone_number', '').strip()

        if user_form.is_valid():
            user_form.save()
            profile.phone_number = phone
            profile.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        user_form = UserProfileForm(instance=user, initial={'phone_number': profile.phone_number})

    return render(request, 'user/profile.html', {
        'user_form': user_form,
        'profile': profile,
    })


@login_required
def change_password_view(request):
    """Change account password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed successfully. Please log in again.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the password errors.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'user/profile.html', {
        'password_form': form,
        'show_password_modal': True
    })


# ==========================================
# USER DASHBOARD & VEHICLE VIEWS
# ==========================================

@login_required
def user_dashboard(request):
    """
    Main user dashboard showing overview metrics, vehicle count,
    active bookings, available slots, and recent activity.
    """
    user = request.user

    # Metrics
    total_vehicles = Vehicle.objects.filter(user=user).count()
    active_bookings = Booking.objects.filter(user=user, status__in=['RESERVED', 'ACTIVE']).count()
    completed_history = Booking.objects.filter(user=user, status='COMPLETED').count()
    available_slots = ParkingSlot.objects.filter(status='AVAILABLE').count()

    # Recent items
    recent_vehicles = Vehicle.objects.filter(user=user)[:4]
    recent_bookings = Booking.objects.filter(user=user).select_related('vehicle', 'parking_slot', 'parking_slot__parking_area')[:5]

    context = {
        'total_vehicles': total_vehicles,
        'active_bookings': active_bookings,
        'completed_history': completed_history,
        'available_slots': available_slots,
        'recent_vehicles': recent_vehicles,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'user/dashboard.html', context)


@login_required
def vehicle_list(request):
    """Display all vehicles owned by the logged-in user."""
    vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, 'user/vehicles.html', {'vehicles': vehicles})


@login_required
def vehicle_add(request):
    """Add a new vehicle for the user."""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()
            messages.success(request, f"Vehicle '{vehicle.vehicle_number}' added successfully.")
            return redirect('vehicle_list')
        else:
            messages.error(request, "Please correct the errors in the vehicle form.")
    else:
        form = VehicleForm()

    return render(request, 'user/vehicle_form.html', {'form': form, 'title': 'Add New Vehicle'})


@login_required
def vehicle_edit(request, pk):
    """Edit an existing vehicle owned by the user."""
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)

    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle '{vehicle.vehicle_number}' updated successfully.")
            return redirect('vehicle_list')
        else:
            messages.error(request, "Please correct the errors in the vehicle form.")
    else:
        form = VehicleForm(instance=vehicle)

    return render(request, 'user/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle', 'vehicle': vehicle})


@login_required
def vehicle_delete(request, pk):
    """Delete a vehicle owned by the user."""
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)

    # Prevent deletion if active booking exists
    if vehicle.bookings.filter(status__in=['RESERVED', 'ACTIVE']).exists():
        messages.error(request, f"Cannot delete vehicle '{vehicle.vehicle_number}' because it has an active or reserved booking.")
        return redirect('vehicle_list')

    if request.method == 'POST':
        num = vehicle.vehicle_number
        vehicle.delete()
        messages.success(request, f"Vehicle '{num}' deleted successfully.")
        return redirect('vehicle_list')

    return render(request, 'user/vehicle_confirm_delete.html', {'vehicle': vehicle})


# ==========================================
# PARKING SLOTS & BOOKINGS
# ==========================================

@login_required
def parking_slots_view(request):
    """
    Visual parking slot grid displaying status badges:
    Available (Green), Occupied (Red), Reserved (Yellow).
    Includes filtering by Parking Area, Vehicle Type, and Status.
    """
    areas = ParkingArea.objects.all()
    slots = ParkingSlot.objects.select_related('parking_area').all()

    # Search & Filter
    area_id = request.GET.get('area')
    vehicle_type = request.GET.get('vehicle_type')
    status = request.GET.get('status')
    search_query = request.GET.get('q', '').strip()

    if area_id:
        slots = slots.filter(parking_area_id=area_id)
    if vehicle_type:
        slots = slots.filter(vehicle_type=vehicle_type)
    if status:
        slots = slots.filter(status=status)
    if search_query:
        slots = slots.filter(
            Q(slot_number__icontains=search_query) |
            Q(parking_area__name__icontains=search_query)
        )

    # Statistics for filter counters
    total_slots_count = ParkingSlot.objects.count()
    available_count = ParkingSlot.objects.filter(status='AVAILABLE').count()
    occupied_count = ParkingSlot.objects.filter(status='OCCUPIED').count()
    reserved_count = ParkingSlot.objects.filter(status='RESERVED').count()

    # Rates for info tooltip/badge
    rates = {rate.vehicle_type: rate.hourly_rate for rate in ParkingRate.objects.all()}

    context = {
        'areas': areas,
        'slots': slots,
        'selected_area': area_id,
        'selected_type': vehicle_type,
        'selected_status': status,
        'search_query': search_query,
        'vehicle_types': Vehicle.VEHICLE_TYPES,
        'total_slots_count': total_slots_count,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'reserved_count': reserved_count,
        'rates': rates,
    }
    return render(request, 'parking/slots.html', context)


@login_required
def booking_create(request):
    """
    Book an available parking slot for a registered vehicle.
    Atomic status update: Slot status changes to RESERVED.
    """
    user_vehicles = Vehicle.objects.filter(user=request.user)
    if not user_vehicles.exists():
        messages.warning(request, "You must register at least one vehicle before booking a parking slot.")
        return redirect('vehicle_add')

    slot_id = request.GET.get('slot_id')
    selected_slot = None
    if slot_id:
        selected_slot = get_object_or_404(ParkingSlot, pk=slot_id)
        if selected_slot.status != 'AVAILABLE':
            messages.error(request, f"Slot {selected_slot.slot_number} is no longer available.")
            return redirect('parking_slots')

    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            slot = form.cleaned_data['parking_slot']

            with transaction.atomic():
                # Re-verify availability inside atomic lock
                locked_slot = ParkingSlot.objects.select_for_update().get(pk=slot.pk)
                if locked_slot.status != 'AVAILABLE':
                    messages.error(request, "Sorry! This slot was just reserved by someone else. Please select another slot.")
                    return redirect('parking_slots')

                booking = form.save(commit=False)
                booking.user = request.user
                booking.status = 'RESERVED'
                booking.save()

                # Update slot status
                locked_slot.status = 'RESERVED'
                locked_slot.save()

            messages.success(
                request,
                f"Booking confirmed! Your booking reference is {booking.booking_reference}. Slot {slot.slot_number} has been reserved."
            )
            return redirect('booking_detail', pk=booking.pk)
        else:
            messages.error(request, "Please correct the errors in the booking form.")
    else:
        form = BookingForm(user=request.user, selected_slot=selected_slot)

    return render(request, 'parking/booking_form.html', {
        'form': form,
        'selected_slot': selected_slot
    })


@login_required
def booking_list(request):
    """List bookings for the logged-in user with status filter."""
    bookings = Booking.objects.filter(user=request.user).select_related('vehicle', 'parking_slot', 'parking_slot__parking_area')

    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    search = request.GET.get('q', '').strip()
    if search:
        bookings = bookings.filter(
            Q(booking_reference__icontains=search) |
            Q(vehicle__vehicle_number__icontains=search) |
            Q(parking_slot__slot_number__icontains=search)
        )

    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'parking/booking_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search': search,
    })


@login_required
def booking_detail(request, pk):
    """View details of a specific booking."""
    booking = get_object_or_404(
        Booking.objects.select_related('vehicle', 'parking_slot', 'parking_slot__parking_area', 'user'),
        pk=pk
    )

    # Permission check: normal user can only view their own booking
    if not (request.user == booking.user or is_staff_or_admin_check(request.user)):
        messages.error(request, "You are not authorized to view this booking.")
        return redirect('dashboard')

    # Associated parking record if checked-in or checked-out
    record = getattr(booking, 'record', None)
    rate = ParkingRate.objects.filter(vehicle_type=booking.vehicle.vehicle_type).first()

    return render(request, 'parking/booking_detail.html', {
        'booking': booking,
        'record': record,
        'rate': rate,
    })


@login_required
def booking_cancel(request, pk):
    """
    Cancel an existing reservation.
    Important rule: Slot status changes back to AVAILABLE.
    """
    booking = get_object_or_404(Booking, pk=pk)

    # Authorization
    if not (request.user == booking.user or is_staff_or_admin_check(request.user)):
        messages.error(request, "You cannot cancel this booking.")
        return redirect('dashboard')

    if booking.status != 'RESERVED':
        messages.error(request, f"Cannot cancel booking in '{booking.get_status_display()}' status.")
        return redirect('booking_detail', pk=booking.pk)

    if request.method == 'POST':
        with transaction.atomic():
            booking.status = 'CANCELLED'
            booking.save()

            slot = booking.parking_slot
            slot.status = 'AVAILABLE'
            slot.save()

        messages.success(request, f"Booking {booking.booking_reference} has been cancelled. Slot {slot.slot_number} is now Available.")
        return redirect('booking_list')

    return render(request, 'parking/booking_confirm_cancel.html', {'booking': booking})


@login_required
def parking_history(request):
    """User's parking history with duration and calculated fees."""
    records = ParkingRecord.objects.filter(booking__user=request.user).select_related(
        'booking', 'booking__vehicle', 'booking__parking_slot', 'booking__parking_slot__parking_area'
    )

    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'parking/history.html', {'page_obj': page_obj})


# ==========================================
# STAFF VEHICLE ENTRY & EXIT MANAGEMENT
# ==========================================

@staff_or_admin_required
def staff_check_in(request):
    """
    Vehicle Entry:
    1. Search booking reference or vehicle number.
    2. Verify booking is in RESERVED status.
    3. Check-In creates ParkingRecord(entry_time=now),
       changes Booking Status to ACTIVE and Slot Status to OCCUPIED.
    """
    query = request.GET.get('query', '').strip()
    booking = None

    if query:
        # Search by exact reference or vehicle number
        booking = Booking.objects.filter(
            Q(booking_reference__iexact=query) |
            Q(vehicle__vehicle_number__iexact=query),
            status='RESERVED'
        ).select_related('vehicle', 'parking_slot', 'user', 'parking_slot__parking_area').first()

        if not booking:
            # Check if already active
            active = Booking.objects.filter(
                Q(booking_reference__iexact=query) |
                Q(vehicle__vehicle_number__iexact=query),
                status='ACTIVE'
            ).first()
            if active:
                messages.warning(request, f"Vehicle '{query}' is already checked in and currently parked in slot {active.parking_slot.slot_number}.")
            else:
                messages.error(request, f"No reserved booking found for '{query}'. Please verify reference or vehicle number.")

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        target_booking = get_object_or_404(Booking, pk=booking_id, status='RESERVED')

        with transaction.atomic():
            target_booking.status = 'ACTIVE'
            target_booking.save()

            slot = target_booking.parking_slot
            slot.status = 'OCCUPIED'
            slot.save()

            # Create entry record
            ParkingRecord.objects.create(
                booking=target_booking,
                entry_time=timezone.now()
            )

        messages.success(
            request,
            f"Check-In Complete! Vehicle {target_booking.vehicle.vehicle_number} checked in to Slot {slot.slot_number}."
        )
        return redirect('staff_check_in')

    return render(request, 'staff/check_in.html', {
        'search_form': StaffSearchForm(initial={'query': query} if query else None),
        'booking': booking,
        'query': query,
    })


@staff_or_admin_required
def staff_check_out(request):
    """
    Vehicle Exit:
    1. Search active vehicle / booking.
    2. Display entry time, duration, and calculate parking fee using ceiling logic.
    3. Check-Out sets exit_time, total_fee, Booking Status to COMPLETED, and Slot Status to AVAILABLE.
    """
    query = request.GET.get('query', '').strip()
    booking = None
    preview_duration = None
    preview_fee = None

    if query:
        booking = Booking.objects.filter(
            Q(booking_reference__iexact=query) |
            Q(vehicle__vehicle_number__iexact=query),
            status='ACTIVE'
        ).select_related('vehicle', 'parking_slot', 'user', 'record', 'parking_slot__parking_area').first()

        if booking and hasattr(booking, 'record'):
            now = timezone.now()
            delta = now - booking.record.entry_time
            seconds = max(0, delta.total_seconds())
            preview_duration = max(1, math.ceil(seconds / 3600))

            rate_obj = ParkingRate.objects.filter(vehicle_type=booking.vehicle.vehicle_type).first()
            rate = rate_obj.hourly_rate if rate_obj else Decimal('50.00')
            preview_fee = Decimal(preview_duration) * rate
        elif not booking:
            messages.error(request, f"No active parked vehicle found for '{query}'.")

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        target_booking = get_object_or_404(Booking, pk=booking_id, status='ACTIVE')

        with transaction.atomic():
            record = target_booking.record
            duration, fee = record.calculate_duration_and_fee(timezone.now())
            record.save()

            target_booking.status = 'COMPLETED'
            target_booking.save()

            slot = target_booking.parking_slot
            slot.status = 'AVAILABLE'
            slot.save()

        messages.success(
            request,
            f"Check-Out Complete! Vehicle {target_booking.vehicle.vehicle_number} exited. Duration: {duration} hr(s). Total Fee: Rs. {fee}."
        )
        return redirect('booking_detail', pk=target_booking.pk)

    return render(request, 'staff/check_out.html', {
        'search_form': StaffSearchForm(initial={'query': query} if query else None),
        'booking': booking,
        'query': query,
        'preview_duration': preview_duration,
        'preview_fee': preview_fee,
    })


# ==========================================
# ADMIN DASHBOARD & MANAGEMENT VIEWS
# ==========================================

@admin_required
def admin_dashboard(request):
    """
    Administrative overview dashboard showing key metrics,
    slot occupancy distribution, today's revenue, and recent activities.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Metrics
    total_users = User.objects.filter(is_superuser=False).count()
    total_vehicles = Vehicle.objects.count()
    total_areas = ParkingArea.objects.count()
    total_slots = ParkingSlot.objects.count()

    available_slots = ParkingSlot.objects.filter(status='AVAILABLE').count()
    occupied_slots = ParkingSlot.objects.filter(status='OCCUPIED').count()
    reserved_slots = ParkingSlot.objects.filter(status='RESERVED').count()

    active_parking = Booking.objects.filter(status='ACTIVE').count()
    completed_parking = Booking.objects.filter(status='COMPLETED').count()

    # Today's Revenue
    today_records = ParkingRecord.objects.filter(exit_time__gte=today_start, total_fee__isnull=False)
    today_revenue = today_records.aggregate(total=Sum('total_fee'))['total'] or Decimal('0.00')

    # Total all-time revenue
    total_revenue = ParkingRecord.objects.filter(total_fee__isnull=False).aggregate(total=Sum('total_fee'))['total'] or Decimal('0.00')

    # Recent bookings
    recent_bookings = Booking.objects.select_related('user', 'vehicle', 'parking_slot').all()[:6]

    context = {
        'total_users': total_users,
        'total_vehicles': total_vehicles,
        'total_areas': total_areas,
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'reserved_slots': reserved_slots,
        'active_parking': active_parking,
        'completed_parking': completed_parking,
        'today_revenue': today_revenue,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


# --- Parking Areas Management ---

@admin_required
def admin_parking_areas(request):
    """Admin view to manage parking areas."""
    areas = ParkingArea.objects.prefetch_related('slots').all()

    if request.method == 'POST':
        form = ParkingAreaForm(request.POST)
        if form.is_valid():
            area = form.save()
            messages.success(request, f"Parking area '{area.name}' created successfully.")
            return redirect('admin_parking_areas')
        else:
            messages.error(request, "Failed to create area. Please correct errors.")
    else:
        form = ParkingAreaForm()

    return render(request, 'admin_dashboard/parking_areas.html', {'areas': areas, 'form': form})


@admin_required
def admin_parking_area_edit(request, pk):
    """Edit parking area."""
    area = get_object_or_404(ParkingArea, pk=pk)
    if request.method == 'POST':
        form = ParkingAreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f"Parking area '{area.name}' updated successfully.")
            return redirect('admin_parking_areas')
    else:
        form = ParkingAreaForm(instance=area)

    return render(request, 'admin_dashboard/parking_area_edit.html', {'form': form, 'area': area})


@admin_required
def admin_parking_area_delete(request, pk):
    """Delete parking area."""
    area = get_object_or_404(ParkingArea, pk=pk)
    if area.slots.filter(status__in=['OCCUPIED', 'RESERVED']).exists():
        messages.error(request, f"Cannot delete '{area.name}' because it contains active or reserved slots.")
        return redirect('admin_parking_areas')

    if request.method == 'POST':
        name = area.name
        area.delete()
        messages.success(request, f"Parking area '{name}' and its slots were deleted.")
        return redirect('admin_parking_areas')

    return render(request, 'admin_dashboard/confirm_delete.html', {
        'object_name': f"Parking Area: {area.name}",
        'cancel_url': 'admin_parking_areas'
    })


# --- Parking Slots Management ---

@admin_required
def admin_parking_slots(request):
    """Admin view to view and add parking slots."""
    slots = ParkingSlot.objects.select_related('parking_area').all()

    # Filter
    area_id = request.GET.get('area')
    if area_id:
        slots = slots.filter(parking_area_id=area_id)

    if request.method == 'POST':
        form = ParkingSlotForm(request.POST)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f"Slot '{slot.slot_number}' created successfully.")
            return redirect('admin_parking_slots')
        else:
            messages.error(request, "Failed to create slot. Check for duplicates or invalid values.")
    else:
        form = ParkingSlotForm()

    areas = ParkingArea.objects.all()
    return render(request, 'admin_dashboard/parking_slots.html', {
        'slots': slots,
        'form': form,
        'areas': areas,
        'selected_area': area_id,
    })


@admin_required
def admin_parking_slot_edit(request, pk):
    """Edit parking slot."""
    slot = get_object_or_404(ParkingSlot, pk=pk)
    if request.method == 'POST':
        form = ParkingSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, f"Slot '{slot.slot_number}' updated successfully.")
            return redirect('admin_parking_slots')
    else:
        form = ParkingSlotForm(instance=slot)

    return render(request, 'admin_dashboard/parking_slot_edit.html', {'form': form, 'slot': slot})


@admin_required
def admin_parking_slot_delete(request, pk):
    """Delete parking slot."""
    slot = get_object_or_404(ParkingSlot, pk=pk)
    if slot.status in ['OCCUPIED', 'RESERVED']:
        messages.error(request, f"Cannot delete slot '{slot.slot_number}' while it is {slot.get_status_display().lower()}.")
        return redirect('admin_parking_slots')

    if request.method == 'POST':
        num = slot.slot_number
        slot.delete()
        messages.success(request, f"Slot '{num}' deleted.")
        return redirect('admin_parking_slots')

    return render(request, 'admin_dashboard/confirm_delete.html', {
        'object_name': f"Slot: {slot.slot_number} ({slot.parking_area.name})",
        'cancel_url': 'admin_parking_slots'
    })


# --- Bookings, Vehicles, Rates, Users ---

@admin_required
def admin_bookings(request):
    """Admin view of all bookings with search and filter."""
    bookings = Booking.objects.select_related('user', 'vehicle', 'parking_slot', 'parking_slot__parking_area').all()

    # Search & filters
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status')

    if search:
        bookings = bookings.filter(
            Q(booking_reference__icontains=search) |
            Q(user__username__icontains=search) |
            Q(vehicle__vehicle_number__icontains=search) |
            Q(parking_slot__slot_number__icontains=search)
        )
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    paginator = Paginator(bookings, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_dashboard/bookings.html', {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
    })


@admin_required
def admin_vehicles(request):
    """Admin view to see all vehicles across the system."""
    vehicles = Vehicle.objects.select_related('user').all()

    search = request.GET.get('q', '').strip()
    vtype = request.GET.get('type')

    if search:
        vehicles = vehicles.filter(
            Q(vehicle_number__icontains=search) |
            Q(user__username__icontains=search) |
            Q(vehicle_brand__icontains=search) |
            Q(vehicle_model__icontains=search)
        )
    if vtype:
        vehicles = vehicles.filter(vehicle_type=vtype)

    paginator = Paginator(vehicles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_dashboard/vehicles.html', {
        'page_obj': page_obj,
        'search': search,
        'vtype': vtype,
        'types': Vehicle.VEHICLE_TYPES,
    })


@admin_required
def admin_rates(request):
    """Admin view to manage hourly parking rates."""
    rates = ParkingRate.objects.all()

    if request.method == 'POST':
        rate_id = request.POST.get('rate_id')
        hourly_rate = request.POST.get('hourly_rate')

        if rate_id and hourly_rate:
            rate = get_object_or_404(ParkingRate, pk=rate_id)
            try:
                rate.hourly_rate = Decimal(hourly_rate)
                rate.save()
                messages.success(request, f"Updated rate for {rate.get_vehicle_type_display()} to Rs. {rate.hourly_rate}/hour.")
            except Exception:
                messages.error(request, "Invalid rate value entered.")
        else:
            form = ParkingRateForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New rate configuration added.")
            else:
                messages.error(request, "Failed to save rate. It may already exist.")
        return redirect('admin_rates')

    form = ParkingRateForm()
    return render(request, 'admin_dashboard/rates.html', {'rates': rates, 'form': form})


@admin_required
def admin_reports(request):
    """
    Generate reports:
    - Daily Parking Report
    - Vehicle Parking Report
    - Booking Report
    - Parking Revenue Report
    Filtered using Django QuerySets by date range, vehicle type, and parking area.
    """
    records = ParkingRecord.objects.select_related(
        'booking', 'booking__user', 'booking__vehicle', 'booking__parking_slot', 'booking__parking_slot__parking_area'
    )

    form = ReportFilterForm(request.GET or None)

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        parking_area = form.cleaned_data.get('parking_area')
        vehicle_type = form.cleaned_data.get('vehicle_type')

        if start_date:
            records = records.filter(entry_time__date__gte=start_date)
        if end_date:
            records = records.filter(entry_time__date__lte=end_date)
        if parking_area:
            records = records.filter(booking__parking_slot__parking_area=parking_area)
        if vehicle_type:
            records = records.filter(booking__vehicle__vehicle_type=vehicle_type)

    # Aggregations
    total_records = records.count()
    completed_records = records.filter(exit_time__isnull=False)
    total_revenue = completed_records.aggregate(total=Sum('total_fee'))['total'] or Decimal('0.00')
    total_hours = completed_records.aggregate(hours=Sum('duration'))['hours'] or 0

    # Vehicle type breakdown
    type_breakdown = (
        records.values('booking__vehicle__vehicle_type')
        .annotate(count=Count('id'), revenue=Sum('total_fee'))
        .order_by('-count')
    )

    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_dashboard/reports.html', {
        'form': form,
        'page_obj': page_obj,
        'total_records': total_records,
        'total_revenue': total_revenue,
        'total_hours': total_hours,
        'type_breakdown': type_breakdown,
    })


@admin_required
def admin_users(request):
    """Admin view to view and manage registered users."""
    users = User.objects.select_related('profile').all().order_by('-date_joined')

    search = request.GET.get('q', '').strip()
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    return render(request, 'admin_dashboard/users.html', {'users': users, 'search': search})


@admin_required
def admin_toggle_user_status(request, pk):
    """Activate or deactivate a user account."""
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj.is_superuser:
        messages.error(request, "Cannot deactivate a superuser account.")
        return redirect('admin_users')

    user_obj.is_active = not user_obj.is_active
    user_obj.save()

    status_str = "activated" if user_obj.is_active else "deactivated"
    messages.success(request, f"User '{user_obj.username}' has been {status_str}.")
    return redirect('admin_users')
