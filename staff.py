from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import db, User, Trek, Booking
from decorators import staff_required

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    trek_data = []
    for trek in assigned_treks:
        booked_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek_data.append({'trek': trek, 'booked_count': booked_count})
    return render_template('staff/dashboard.html', trek_data=trek_data)


@staff_bp.route('/trek/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@staff_required
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    booked_count = trek.booked_count()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_slots':
            raw = request.form.get('total_slots', '')
            try:
                new_total = int(raw)
            except (TypeError, ValueError):
                flash('Please enter a valid number for total slots.', 'danger')
                return render_template('staff/trek_detail.html', trek=trek, booked_count=booked_count)
            if new_total < 1:
                flash('Total slots must be at least 1.', 'danger')
                return render_template('staff/trek_detail.html', trek=trek, booked_count=booked_count)
            if new_total < booked_count:
                flash(f'Cannot set slots below current bookings ({booked_count}).', 'danger')
                return render_template('staff/trek_detail.html', trek=trek, booked_count=booked_count)
            trek.total_slots = new_total
            trek.available_slots = new_total - booked_count
            db.session.commit()
            flash('Slots updated.', 'success')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))

        elif action == 'update_status':
            new_status = request.form.get('status')
            allowed = ['Approved', 'Open', 'Closed', 'Completed']
            if new_status not in allowed:
                flash('Invalid status selected.', 'danger')
                return render_template('staff/trek_detail.html', trek=trek, booked_count=booked_count)
            trek.status = new_status
            if new_status == 'Completed':
                Booking.query.filter_by(trek_id=trek.id, status='Booked').update({'status': 'Completed'})
            trek.available_slots = trek.total_slots - booked_count
            db.session.commit()
            flash(f'Trek status updated to {new_status}.', 'success')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))

        elif action == 'start_trek':
            if trek.status == 'Open':
                trek.status = 'Started'
                db.session.commit()
                flash('Trek marked as Started.', 'success')
            else:
                flash('Only Open treks can be started.', 'warning')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))

        elif action == 'complete_trek':
            trek.status = 'Completed'
            Booking.query.filter_by(trek_id=trek.id, status='Booked').update({'status': 'Completed'})
            trek.available_slots = trek.total_slots - booked_count
            db.session.commit()
            flash('Trek marked as Completed.', 'success')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))

        flash('Unknown action.', 'warning')

    return render_template('staff/trek_detail.html', trek=trek, booked_count=booked_count)


@staff_bp.route('/trek/<int:trek_id>/participants')
@login_required
@staff_required
def participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != current_user.id:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))
    bookings = Booking.query.filter_by(trek_id=trek_id).order_by(Booking.booking_date.desc()).all()
    return render_template('staff/participants.html', trek=trek, bookings=bookings)


@staff_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@staff_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not full_name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('staff/profile.html')

        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash('Email already in use.', 'danger')
            return render_template('staff/profile.html')

        current_user.full_name = full_name
        current_user.phone     = phone
        current_user.email     = email

        if password:
            if password != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('staff/profile.html')
            current_user.set_password(password)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('staff.profile'))

    return render_template('staff/profile.html')
