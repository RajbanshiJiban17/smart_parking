# Smart Parking Management System

A complete, responsive, and secure **Web-Based Smart Parking Management System** developed for a **Bachelor 6th Semester Academic Project**.

Built strictly using **Python, Django, SQLite, HTML5, CSS3, JavaScript, and Bootstrap 5**, with zero external dependencies, no IoT hardware, and no online payment gateway requirements.

---

## 1. Academic Project Overview

* **Project Title:** Smart Parking Management System
* **Project Type:** Web-Based Parking & Slot Reservation System
* **Academic Level:** Bachelor – 6th Semester
* **Architecture:** Django MVC / MVT (Model-View-Template)
* **Design Pattern:** Layered ORM, Role-Based Access Control (RBAC), and Atomic Transactions

### Key Objectives
1. **Digitize Slot Management:** Replace paper registers with a centralized web system for monitoring parking bay occupancy.
2. **Visual Bay Mapping:** Real-time visual representation of slots across multiple parking areas (Available in Green, Occupied in Red, Reserved in Yellow).
3. **Vehicle Entry & Exit Operations:** Streamlined check-in and check-out workflows for parking attendants.
4. **Automated Fee Calculation:** Automated duration computation with academic ceiling logic (`math.ceil()`).
5. **Auditing & Reporting:** QuerySet-driven reporting filtered by date, vehicle category, and area.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.12, Django 5.x / 6.x | Core framework, routing, ORM, authentication |
| **Database** | SQLite 3 | Lightweight, zero-configuration relational database |
| **Frontend Framework** | Bootstrap 5.3 + Bootstrap Icons | Responsive grid system, stat cards, alerts, modals |
| **Custom Styling** | Vanilla CSS3 (`style.css`, `responsive.css`) | Custom card designs, parking bay layout, sidebar |
| **Client-Side Logic** | Vanilla JavaScript (`main.js`) | Offcanvas sidebar, auto-dismiss alerts, confirmation dialogs |
| **Security** | Django CSRF, PBKDF2 Password Hashing, Decorators | Role verification and form protection |

> **Academic Restriction Compliance:** Strictly adheres to project constraints: **NO IoT sensors, NO Arduino/Raspberry Pi, NO AI/ML, NO third-party payment gateways (Khalti/eSewa/Stripe), and NO React/Node.js dependencies**.

---

## 3. User Roles & Default Test Credentials

The system includes three distinct roles with customized access levels:

| Role | Username | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full control: areas, slots, rates, all bookings, vehicle directory, reports, user accounts |
| **Parking Staff** | `staff` | `staff123` | Operational access: Vehicle Check-In, Vehicle Check-Out, verification of bookings |
| **Driver / Customer** | `driver` | `driver123` | Self-service portal: register vehicles, search available bays, book slots, cancel reservations, view history |

---

## 4. System Workflow & Business Rules

```
[Driver]
   │
   ├─► Register & Log In
   ├─► Add Vehicle (Car, Motorcycle, Bicycle, Other)
   ├─► Browse Visual Slot Grid (Filter by Area & Type)
   └─► Create Reservation ──────┐
                                │ Slot Status becomes 'RESERVED'
                                ▼
                        [Staff / Attendant]
                                │
                                ├─► Check-In (Search Reference or Plate)
                                │     └─► Slot becomes 'OCCUPIED'
                                │     └─► Booking becomes 'ACTIVE'
                                │     └─► Records Entry Timestamp
                                │
                                ├─► Vehicle Parks...
                                │
                                └─► Check-Out (Search Plate or Reference)
                                      ├─► Calculates Elapsed Time (math.ceil)
                                      ├─► Computes Fee (Duration × Hourly Rate)
                                      ├─► Marks Booking 'COMPLETED'
                                      └─► Frees Slot back to 'AVAILABLE'
```

### Database Consistency Rules
* **On Booking:** `ParkingSlot.status` $\rightarrow$ `RESERVED`, `Booking.status` $\rightarrow$ `RESERVED`
* **On Cancellation:** `ParkingSlot.status` $\rightarrow$ `AVAILABLE`, `Booking.status` $\rightarrow$ `CANCELLED`
* **On Check-In:** `ParkingSlot.status` $\rightarrow$ `OCCUPIED`, `Booking.status` $\rightarrow$ `ACTIVE`, `ParkingRecord.entry_time` recorded
* **On Check-Out:** `ParkingSlot.status` $\rightarrow$ `AVAILABLE`, `Booking.status` $\rightarrow$ `COMPLETED`, `duration` and `total_fee` stored

### Parking Fee Ceiling Formula
Parking fees are calculated using standard academic ceiling logic:
$$\text{Duration (hours)} = \max\left(1, \left\lceil \frac{\text{Exit Time} - \text{Entry Time}}{3600} \right\rceil\right)$$
$$\text{Total Fee} = \text{Duration} \times \text{Hourly Rate}$$

*Example: 1 hour and 15 minutes of parking for a Car (Rs. 50/hour):*
$$\lceil 75 \text{ mins} / 60 \text{ mins} \rceil = 2 \text{ hours} \times \text{Rs. 50} = \text{Rs. 100.00}$$

---

## 5. Project Directory Structure

```text
smart_parking/
│
├── manage.py                          # Django management script
├── requirements.txt                   # Dependency manifest (Django, Pillow)
├── README.md                          # Project documentation and presentation guide
├── db.sqlite3                         # SQLite database file
│
├── smart_parking/                     # Project configuration package
│   ├── __init__.py
│   ├── settings.py                    # Settings, apps, static paths, auth redirects
│   ├── urls.py                        # Root URL routing
│   ├── wsgi.py                        # WSGI entry point
│   └── asgi.py                        # ASGI entry point
│
├── parking/                           # Core Parking Application
│   ├── __init__.py
│   ├── admin.py                       # Django admin registrations with filters & search
│   ├── apps.py                        # App configuration
│   ├── forms.py                       # ModelForms with Bootstrap styling & validations
│   ├── models.py                      # UserProfile, Vehicle, ParkingArea, Slot, Rate, Booking, Record
│   ├── tests.py                       # Unit & integration test cases
│   ├── urls.py                        # Clean app URL routing
│   ├── views.py                       # Role-based views, transactional updates, reports
│   │
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py           # Command to seed demo users, areas, slots & bookings
│   │
│   └── migrations/
│       └── 0001_initial.py            # Initial database migration
│
├── templates/                         # HTML5 Django Templates
│   ├── base.html                      # Base skeleton with Bootstrap 5 CDN & alerts
│   │
│   ├── includes/
│   │   ├── navbar.html                # Top navigation header & user profile dropdown
│   │   ├── sidebar.html               # Responsive role-aware sidebar
│   │   └── footer.html                # Footer info
│   │
│   ├── registration/
│   │   ├── login.html                 # Login page with demo credentials quick-card
│   │   └── register.html              # User registration with phone number & full name
│   │
│   ├── user/
│   │   ├── dashboard.html             # Driver dashboard with 4 KPI cards & recent bookings
│   │   ├── profile.html               # Profile details & password change
│   │   ├── vehicles.html              # Vehicle management list
│   │   ├── vehicle_form.html          # Add / edit vehicle
│   │   └── vehicle_confirm_delete.html# Confirm vehicle deletion
│   │
│   ├── parking/
│   │   ├── slots.html                 # Visual slot grid (Green, Red, Yellow badges)
│   │   ├── booking_form.html          # 4-step slot reservation form
│   │   ├── booking_list.html          # Driver bookings directory & filter
│   │   ├── booking_detail.html        # Printable confirmation slip & fee receipt
│   │   ├── booking_confirm_cancel.html# Reservation cancellation dialog
│   │   └── history.html               # User parking history with duration & fee
│   │
│   ├── staff/
│   │   ├── check_in.html              # Attendant vehicle entry verification
│   │   └── check_out.html             # Attendant check-out with automatic fee preview
│   │
│   └── admin_dashboard/
│       ├── dashboard.html             # Master metrics, revenue & occupancy counters
│       ├── parking_areas.html         # Area management & slot counters
│       ├── parking_area_edit.html     # Edit parking area
│       ├── parking_slots.html         # Bay management & status overrides
│       ├── parking_slot_edit.html     # Edit bay number & status
│       ├── bookings.html              # All system bookings audit table
│       ├── vehicles.html              # System-wide vehicle directory
│       ├── rates.html                 # Category-based hourly rate configuration
│       ├── reports.html               # Filtered financial & duration reports
│       ├── users.html                 # User accounts list & active/inactive toggle
│       └── confirm_delete.html        # Generic admin delete confirmation
│
└── static/                            # Static Assets
    ├── css/
    │   ├── style.css                  # Modern clean stylesheet & card layouts
    │   └── responsive.css             # Mobile & tablet breakpoints
    └── js/
        └── main.js                    # Auto-dismiss alerts, offcanvas sidebar, confirmations
```

---

## 6. Installation & Execution Guide

### Prerequisites
* Python 3.10+ installed on your computer.

### Step 1: Clone or Navigate to Project Folder
```bash
cd c:\Users\User\Desktop\SmartParkingProject\smart_parking
```

### Step 2: (Optional) Create and Activate Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Seed Demo Sample Data
Populate the database with pre-configured parking areas, 22 parking bays, rates, and test accounts:
```bash
python manage.py seed_data
```

### Step 6: Run Automated Tests
Verify all business rules, models, and views:
```bash
python manage.py test
```

### Step 7: Start Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

---

## 7. URL Route Map

| URL Pattern | View Name | Access | Purpose |
| :--- | :--- | :--- | :--- |
| `/` | `home` | Authenticated | Redirects to Driver or Admin Dashboard |
| `/login/` | `login` | Public | Sign in to account |
| `/register/` | `register` | Public | Create new Driver account |
| `/logout/` | `logout` | Authenticated | End current session |
| `/dashboard/` | `dashboard` | Driver / Any | Driver metrics & active bookings |
| `/vehicles/` | `vehicle_list` | Driver | View registered vehicles |
| `/vehicles/add/` | `vehicle_add` | Driver | Add vehicle with plate validation |
| `/parking-slots/` | `parking_slots` | Driver / Any | Visual bay map with live filters |
| `/bookings/create/` | `booking_create` | Driver | Reserve bay for vehicle |
| `/bookings/<id>/` | `booking_detail` | Driver / Staff / Admin | Printable confirmation slip |
| `/history/` | `parking_history` | Driver | Historical durations and fees |
| `/staff/check-in/` | `staff_check_in` | Staff / Admin | Search and check in arriving vehicle |
| `/staff/check-out/` | `staff_check_out` | Staff / Admin | Search, compute fee, and check out |
| `/admin-dashboard/` | `admin_dashboard` | Admin | High-level metrics and revenue |
| `/admin-dashboard/parking-areas/` | `admin_parking_areas` | Admin | Manage parking zones |
| `/admin-dashboard/parking-slots/` | `admin_parking_slots` | Admin | Manage bays and statuses |
| `/admin-dashboard/rates/` | `admin_rates` | Admin | Manage hourly rates |
| `/admin-dashboard/users/` | `admin_users` | Admin | Activate/Deactivate users |
| `/reports/` | `admin_reports` | Admin | Filterable revenue & duration reports |

---

## 8. Academic Viva & Defense Questions

**Q1: Why did you choose SQLite over MySQL or PostgreSQL for this project?**
> *Answer:* For a 6th-semester academic project, SQLite provides a zero-configuration, serverless, self-contained relational database bundled directly with Python. It completely satisfies ACID requirements while making the project instantly portable and runnable on any examination computer without external database service configuration.

**Q2: How does the system prevent double booking of the same slot?**
> *Answer:* Double booking is prevented at both the database and application levels:
> 1. In `BookingForm`, slots are strictly validated so only bays with `status='AVAILABLE'` can be submitted.
> 2. In `views.booking_create`, database operations are wrapped in `transaction.atomic()` with `select_for_update()` row locking to eliminate race conditions.

**Q3: How are partial hours handled when calculating parking charges?**
> *Answer:* As specified in parking management practices and project requirements, partial hours are rounded up using Python's `math.ceil()`. For example, 1 hour 10 minutes equals 70 minutes; $70 / 60 = 1.166$, which rounds up to 2 hours. A minimum floor of 1 hour is enforced.

**Q4: How is Role-Based Access Control (RBAC) enforced?**
> *Answer:* Custom Python decorators (`@admin_required`, `@staff_or_admin_required`) check the `UserProfile.role` field and user flags (`is_staff`, `is_superuser`). If an unauthorized driver attempts to access `/admin-dashboard/` or staff URLs, they are safely redirected with a user-friendly error message.

---

## 9. Future Enhancements
* Automated license plate recognition (ALPR) using computer vision.
* SMS or WhatsApp push notifications for reservation reminders.
* Integration of QR code scanning on entry/exit gate kiosks.
* Multi-story visual 3D parking layout map.
