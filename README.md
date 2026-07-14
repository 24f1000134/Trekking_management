# 🏔️ TrekTheHills — Trekking Management System

A Flask web application for managing treks, staff, and bookings — built around three distinct roles (**Admin**, **Staff**, and **User**) each with their own dashboard and permissions.

## Overview

TrekTheHills lets an organization publish treks, assign staff to lead them, and let users browse and book available slots. Admins have full control over treks, staff approval, and user moderation; staff manage the treks assigned to them (slots, status, participants); users browse open treks and manage their own bookings.

## Features

### Admin
- Dashboard with counts of treks, users, staff, bookings, and pending staff approvals
- Create, edit, delete treks — set difficulty, duration, altitude, slots, price, dates, and assign staff
- Approve or blacklist staff registrations
- Search and blacklist users
- View all bookings across the platform

### Staff
- Dashboard listing treks assigned to them with live booked-slot counts
- Update total slots (bounded by existing bookings) and trek status (`Approved` → `Open` → `Started` → `Completed`/`Closed`)
- View participant list and booking notes for each assigned trek

### User
- Browse open treks with search/filter by name, location, and difficulty
- View trek details and available slots, and book a spot
- Manage bookings — view history and cancel active bookings
- Edit profile (name, phone, email, password)

### Auth
- Separate registration flows for regular users (auto-approved) and staff (requires admin approval)
- Session-based login via Flask-Login, with role-based redirects and blacklist/approval checks at login

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Flask 3.0, Flask-Login, Flask-SQLAlchemy |
| Database   | SQLite (`instance/trekking.db`) |
| Frontend   | Jinja2 templates, custom CSS (no JS framework) |
| Auth       | Werkzeug password hashing + session-based login |

## Project Structure

```
Trekking_management/
├── app.py               # App factory, blueprint registration, seeds default admin
├── models.py             # User, Trek, Booking models
├── auth.py                # Login / register / staff-register / logout routes
├── admin.py               # Admin blueprint: treks, staff, users, bookings
├── staff.py                # Staff blueprint: assigned treks, participants
├── user.py                  # User blueprint: browse treks, book, profile
├── decorators.py             # Role-based access decorators
├── templates/                 # Jinja2 templates (auth/, admin/, staff/, User/)
├── static/css/                 # cards, dashboard, forms, navbar, sidebar, utilities
└── instance/trekking.db          # SQLite database (auto-created)
```

## Data Model

- **User** — `username`, `email`, `full_name`, `phone`, `role` (`admin`/`staff`/`user`), `is_approved`, `is_blacklisted`
- **Trek** — `name`, `location`, `difficulty`, `duration_days`, `altitude`, `total_slots`/`available_slots`, `price`, `start_date`/`end_date`, `status` (`Pending`/`Approved`/`Open`/`Started`/`Closed`/`Completed`), `assigned_staff_id`
- **Booking** — `user_id`, `trek_id`, `status` (`Booked`/`Cancelled`/`Completed`), `notes`

## Getting Started

### Prerequisites
- Python 3.10+

### Installation

```bash
git clone <repo-url>
cd Trekking_management
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

The app starts at `http://127.0.0.1:5000` and creates `instance/trekking.db` automatically on first run.

