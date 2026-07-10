from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, logout_user, current_user

from models import db, User, Trek, Booking
from decorators import user_required

user_bp = Blueprint('user', __name__)


@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    if current_user.is_blacklisted:
        flash('Your account has been blacklisted. Contact admin.', 'danger')
        logout_user()
        return redirect(url_for('auth.login'))

    open_treks   = Trek.query.filter_by(status='Open').order_by(Trek.start_date).limit(6).all()
    my_bookings  = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).limit(5).all()
    total_booked = Booking.query.filter_by(user_id=current_user.id, status='Booked').count()
    total_history = Booking.query.filter_by(user_id=current_user.id).count()
    return render_template('user/dashboard.html',
                           open_treks=open_treks,
                           my_bookings=my_bookings,
                           total_booked=total_booked,
                           total_history=total_history)


@user_bp.route('/treks')
@login_required
@user_required
def treks():
    q          = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '')
    location   = request.args.get('location', '')

    query = Trek.query.filter_by(status='Open')
    if q:
        query = query.filter(Trek.name.ilike(f'%{q}%') | Trek.location.ilike(f'%{q}%'))
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))

    all_treks = query.order_by(Trek.start_date).all()
    
    # Simple loop instead of set comprehension
    open_treks = Trek.query.filter_by(status='Open').all()
    location_set = set()
    for t in open_treks:
        location_set.add(t.location)
    locations = sorted(list(location_set))

    # Simple loop instead of set comprehension
    user_bookings = Booking.query.filter_by(user_id=current_user.id, status='Booked').all()
    booked_trek_ids = []
    for b in user_bookings:
        booked_trek_ids.append(b.trek_id)

    return render_template('user/treks.html', treks=all_treks,
                           q=q, difficulty=difficulty, location=location,
                           locations=locations, booked_trek_ids=booked_trek_ids)


@user_bp.route('/trek/<int:trek_id>')
@login_required
@user_required
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    already_booked = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek_id, status='Booked').first()
    return render_template('user/trek_detail.html',
                           trek=trek,
                           already_booked=already_booked,
                           slots_left=trek.available_slots)


@user_bp.route('/trek/<int:trek_id>/book', methods=['POST'])
@login_required
@user_required
def book_trek(trek_id):
    if current_user.is_blacklisted:
        flash('Your account is blacklisted. Cannot book.', 'danger')
        return redirect(url_for('user.treks'))

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('user.treks'))

    if trek.available_slots <= 0:
        flash('No slots available for this trek.', 'danger')
        return redirect(url_for('user.treks'))

    existing = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek_id, status='Booked').first()
    if existing:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('user.bookings'))

    try:
        booking = Booking(
            user_id=current_user.id,
            trek_id=trek_id,
            status='Booked',
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(booking)
        trek.available_slots = trek.available_slots - 1
        db.session.commit()
        flash(f'Successfully booked "{trek.name}".', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not complete booking. Please try again.', 'danger')

    return redirect(url_for('user.bookings'))


@user_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@user_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('user.bookings'))
    if booking.status != 'Booked':
        flash('Only active bookings can be cancelled.', 'warning')
        return redirect(url_for('user.bookings'))
    booking.status = 'Cancelled'
    booking.trek.available_slots = booking.trek.available_slots + 1
    db.session.commit()
    flash('Booking cancelled.', 'info')
    return redirect(url_for('user.bookings'))


@user_bp.route('/bookings')
@login_required
@user_required
def bookings():
    my_bookings = Booking.query.filter_by(user_id=current_user.id)\
                               .order_by(Booking.booking_date.desc()).all()
    return render_template('user/bookings.html', bookings=my_bookings)


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@user_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not full_name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('user/profile.html')

        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash('Email already in use.', 'danger')
            return render_template('user/profile.html')

        current_user.full_name = full_name
        current_user.phone     = phone
        current_user.email     = email

        if password:
            if password != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('user/profile.html')
            current_user.set_password(password)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html')
