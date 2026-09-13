from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import UserProfile, Vehicle, ParkingArea, ParkingSlot, ParkingRate, Booking, ParkingRecord


class UserRegistrationForm(forms.ModelForm):
    """
    User registration form with full name, username, email, phone, and password confirmation.
    """
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (e.g. 98XXXXXXXX)'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 6 characters)'}),
        min_length=6,
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a unique username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please re-enter.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """
    Form for updating profile details.
    """
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailInput(attrs={'class': 'form-control'})
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class VehicleForm(forms.ModelForm):
    """
    Form for adding or editing a vehicle.
    """
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'vehicle_type', 'vehicle_brand', 'vehicle_model']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BA-02-PA-5678'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Toyota, Honda, Yamaha'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Corolla, Civic, FZ'}),
        }

    def clean_vehicle_number(self):
        number = self.cleaned_data.get('vehicle_number', '').strip().upper()
        # Ensure uniqueness excluding the current instance if editing
        qs = Vehicle.objects.filter(vehicle_number__iexact=number)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"A vehicle with number '{number}' is already registered in the system.")
        return number


class ParkingAreaForm(forms.ModelForm):
    """
    Admin form to create or edit parking areas.
    """
    class Meta:
        model = ParkingArea
        fields = ['name', 'location', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Campus Parking'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Block A Gate 1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description and guidelines...'}),
        }


class ParkingSlotForm(forms.ModelForm):
    """
    Admin form to create or edit parking slots.
    """
    class Meta:
        model = ParkingSlot
        fields = ['parking_area', 'slot_number', 'vehicle_type', 'status']
        widgets = {
            'parking_area': forms.Select(attrs={'class': 'form-select'}),
            'slot_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A-01, B-12'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get('parking_area')
        slot_number = cleaned_data.get('slot_number')

        if area and slot_number:
            qs = ParkingSlot.objects.filter(parking_area=area, slot_number__iexact=slot_number)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"Slot number '{slot_number}' already exists in '{area.name}'.")
        return cleaned_data


class ParkingRateForm(forms.ModelForm):
    """
    Admin form to set hourly parking rates.
    """
    class Meta:
        model = ParkingRate
        fields = ['vehicle_type', 'hourly_rate']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50.00', 'step': '0.50'}),
        }


class BookingForm(forms.ModelForm):
    """
    Form for drivers to reserve an available parking slot.
    Dynamically scopes vehicles to current user and validates slot availability and type compatibility.
    """
    class Meta:
        model = Booking
        fields = ['vehicle', 'parking_slot', 'booking_date', 'expected_arrival_time']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehicle'}),
            'parking_slot': forms.Select(attrs={'class': 'form-select', 'id': 'id_parking_slot'}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_arrival_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        selected_slot = kwargs.pop('selected_slot', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(user=user)

        # By default only show available slots
        available_slots = ParkingSlot.objects.filter(status='AVAILABLE')
        if selected_slot:
            self.fields['parking_slot'].queryset = ParkingSlot.objects.filter(pk=selected_slot.pk)
            self.fields['parking_slot'].initial = selected_slot
        else:
            self.fields['parking_slot'].queryset = available_slots

        # Default date to today
        self.fields['booking_date'].initial = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['expected_arrival_time'].initial = timezone.localtime().strftime('%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        slot = cleaned_data.get('parking_slot')
        booking_date = cleaned_data.get('booking_date')

        if booking_date and booking_date < timezone.localdate():
            self.add_error('booking_date', "Booking date cannot be in the past.")

        if slot and slot.status != 'AVAILABLE':
            self.add_error('parking_slot', f"Slot {slot.slot_number} is currently {slot.get_status_display().lower()} and cannot be booked.")

        if vehicle and slot:
            if vehicle.vehicle_type != slot.vehicle_type:
                self.add_error(
                    'parking_slot',
                    f"Slot vehicle type ({slot.get_vehicle_type_display()}) does not match your vehicle type ({vehicle.get_vehicle_type_display()})."
                )

        return cleaned_data


class StaffSearchForm(forms.Form):
    """
    Search form for staff check-in / check-out.
    """
    query = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter Booking Reference (e.g. SP-2026-...) or Vehicle Number',
            'autofocus': 'autofocus'
        })
    )


class ReportFilterForm(forms.Form):
    """
    Filter form for administrative reports.
    """
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    parking_area = forms.ModelChoiceField(
        queryset=ParkingArea.objects.all(),
        required=False,
        empty_label="-- All Parking Areas --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    vehicle_type = forms.ChoiceField(
        choices=[('', '-- All Vehicle Types --')] + Vehicle.VEHICLE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
