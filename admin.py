from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import db, User, Trek, Booking
from decorators import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_treks    = Trek.query.count()
    total_users    = User.query.filter_by(role='user').count()
    total_staff    = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff  = User.query.filter_by(role='staff', is_approved=False).count()
    recent_treks   = Trek.query.order_by(Trek.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_treks=total_treks,
                           total_users=total_users,
                           total_staff=total_staff,
                           total_bookings=total_bookings,
                           pending_staff=pending_staff,
                           recent_treks=recent_treks,
                           recent_bookings=recent_bookings)


# Trek Management 
@admin_bp.route('/treks')
@login_required
@admin_required
def treks():
    q = request.args.get('q', '').strip()
    query = Trek.query
    if q:
        if q.isdigit():
            query = query.filter((Trek.name.ilike(f'%{q}%')) | (Trek.location.ilike(f'%{q}%')) | (Trek.id == int(q)))
        else:
            query = query.filter((Trek.name.ilike(f'%{q}%')) | (Trek.location.ilike(f'%{q}%')))
    all_treks = query.order_by(Trek.created_at.desc()).all()
    return render_template('admin/treks.html', treks=all_treks, q=q)


@admin_bp.route('/treks/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trek():
    staff_list = User.query.filter_by(role='staff', is_approved=True, is_blacklisted=False).all()
    if request.method == 'POST':
        try:
            name          = request.form['name'].strip()
            location      = request.form['location'].strip()
            difficulty    = request.form['difficulty']
            duration_days = int(request.form['duration_days'])
            total_slots   = int(request.form['total_slots'])
            altitude      = int(request.form['altitude'])
            price         = float(request.form.get('price', 0))
            start_date    = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date      = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            description   = request.form.get('description', '').strip()
            staff_id      = request.form.get('assigned_staff_id') or None
      
            if staff_id:
                staff_id = int(staff_id)

            trek = Trek(
                name=name, location=location, difficulty=difficulty,
                duration_days=duration_days, total_slots=total_slots, altitude=altitude,
                available_slots=total_slots, price=price, 
                start_date=start_date, end_date=end_date,
                description=description, assigned_staff_id=staff_id,
                status='Pending'
            )
            db.session.add(trek)
            db.session.commit()
            flash(f'Trek "{name}" created successfully.', 'success')
