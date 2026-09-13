from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path('', views.user_dashboard, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),

    # User Dashboard & Vehicles
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_add, name='vehicle_add'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),

    # Parking Slots & Booking
    path('parking-slots/', views.parking_slots_view, name='parking_slots'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/create/', views.booking_create, name='booking_create'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('history/', views.parking_history, name='parking_history'),

    # Staff Check-In & Check-Out
    path('staff/check-in/', views.staff_check_in, name='staff_check_in'),
    path('staff/check-out/', views.staff_check_out, name='staff_check_out'),

    # Admin Dashboard & Management
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/parking-areas/', views.admin_parking_areas, name='admin_parking_areas'),
    path('admin-dashboard/parking-areas/<int:pk>/edit/', views.admin_parking_area_edit, name='admin_parking_area_edit'),
    path('admin-dashboard/parking-areas/<int:pk>/delete/', views.admin_parking_area_delete, name='admin_parking_area_delete'),
    path('admin-dashboard/parking-slots/', views.admin_parking_slots, name='admin_parking_slots'),
    path('admin-dashboard/parking-slots/<int:pk>/edit/', views.admin_parking_slot_edit, name='admin_parking_slot_edit'),
    path('admin-dashboard/parking-slots/<int:pk>/delete/', views.admin_parking_slot_delete, name='admin_parking_slot_delete'),
    path('admin-dashboard/bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-dashboard/vehicles/', views.admin_vehicles, name='admin_vehicles'),
    path('admin-dashboard/rates/', views.admin_rates, name='admin_rates'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/users/<int:pk>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),

    # Reports
    path('reports/', views.admin_reports, name='admin_reports'),
]
