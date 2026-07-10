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
