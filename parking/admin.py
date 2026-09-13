from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Vehicle, ParkingArea, ParkingSlot, ParkingRate, Booking, ParkingRecord


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'profile__role')

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone_number')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'user', 'vehicle_type', 'vehicle_brand', 'vehicle_model', 'created_at')
    list_filter = ('vehicle_type', 'created_at')
    search_fields = ('vehicle_number', 'vehicle_brand', 'vehicle_model', 'user__username')


@admin.register(ParkingArea)
class ParkingAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'total_slots', 'available_slots_count', 'occupied_slots_count', 'reserved_slots_count', 'created_at')
    search_fields = ('name', 'location')


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'parking_area', 'vehicle_type', 'status')
    list_filter = ('parking_area', 'vehicle_type', 'status')
    search_fields = ('slot_number', 'parking_area__name')


@admin.register(ParkingRate)
class ParkingRateAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type', 'hourly_rate')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'vehicle', 'parking_slot', 'booking_date', 'expected_arrival_time', 'status', 'created_at')
    list_filter = ('status', 'booking_date', 'parking_slot__parking_area')
    search_fields = ('booking_reference', 'user__username', 'vehicle__vehicle_number', 'parking_slot__slot_number')


@admin.register(ParkingRecord)
class ParkingRecordAdmin(admin.ModelAdmin):
    list_display = ('booking', 'entry_time', 'exit_time', 'duration', 'total_fee')
    list_filter = ('entry_time', 'exit_time')
    search_fields = ('booking__booking_reference', 'booking__vehicle__vehicle_number')
