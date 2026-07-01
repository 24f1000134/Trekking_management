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
            return redirect(url_for('admin.treks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating trek: {str(e)}', 'danger')

    return render_template('admin/trek_form.html', trek=None, staff_list=staff_list, action='Add')


@admin_bp.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_list = User.query.filter_by(role='staff', is_approved=True, is_blacklisted=False).all()

    if request.method == 'POST':
        try:
            trek.name          = request.form['name'].strip()
            trek.location      = request.form['location'].strip()
            trek.difficulty    = request.form['difficulty']
            trek.duration_days = int(request.form['duration_days'])
            new_total = int(request.form['total_slots'])
            if new_total < trek.booked_count():
                flash(f'Cannot set slots below current bookings ({trek.booked_count()}).', 'danger')
                return render_template('admin/trek_form.html', trek=trek, staff_list=staff_list, action='Edit')
            trek.total_slots 	= new_total
            trek.altitude       = int(request.form['altitude'])
            trek.available_slots = new_total - trek.booked_count()
            trek.price         = float(request.form.get('price', 0))
            trek.start_date    = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            trek.end_date      = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            trek.description   = request.form.get('description', '').strip()
            trek.status        = request.form['status']
            staff_id           = request.form.get('assigned_staff_id') or None
            trek.assigned_staff_id = int(staff_id) if staff_id else None
            db.session.commit()
            flash(f'Trek "{trek.name}" updated.', 'success')
            return redirect(url_for('admin.treks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating trek: {str(e)}', 'danger')

    return render_template('admin/trek_form.html', trek=trek, staff_list=staff_list, action='Edit')


@admin_bp.route('/treks/<int:trek_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek.id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash(f'Trek "{trek.name}" deleted.', 'warning')
    return redirect(url_for('admin.treks'))


# Staff Management
@admin_bp.route('/staff')
@login_required
@admin_required
def staff():
    q = request.args.get('q', '').strip()
    query = User.query.filter_by(role='staff')
    if q:
        if q.isdigit():
            query = query.filter((User.full_name.ilike(f'%{q}%')) | (User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%')) | (User.id == int(q)))
        else:
            query = query.filter((User.full_name.ilike(f'%{q}%')) | (User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%')))
    staff_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/staff.html', staff_list=staff_list, q=q)


@admin_bp.route('/staff/<int:staff_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_staff(staff_id):
    member = User.query.get_or_404(staff_id)
    if member.role != 'staff':
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin.staff'))
    member.is_approved = True
    db.session.commit()
    flash(f'Staff "{member.full_name}" approved.', 'success')
    return redirect(url_for('admin.staff'))


@admin_bp.route('/staff/<int:staff_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_staff(staff_id):
    member = User.query.get_or_404(staff_id)
    if member.role != 'staff':
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin.staff'))
    member.is_blacklisted = not member.is_blacklisted
    db.session.commit()
    status = 'blacklisted' if member.is_blacklisted else 'reinstated'
    flash(f'Staff "{member.full_name}" {status}.', 'warning')
    return redirect(url_for('admin.staff'))


# User Management
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    q = request.args.get('q', '').strip()
    query = User.query.filter_by(role='user')
    if q:
        if q.isdigit():
            query = query.filter((User.full_name.ilike(f'%{q}%')) | (User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%')) | (User.id == int(q)))
        else:
            query = query.filter((User.full_name.ilike(f'%{q}%')) | (User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%')))
    user_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/user.html', users=user_list, q=q)


@admin_bp.route('/users/<int:user_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_user(user_id):
    u = User.query.get_or_404(user_id)
    u.is_blacklisted = not u.is_blacklisted
    db.session.commit()
    status = 'blacklisted' if u.is_blacklisted else 'reinstated'
    flash(f'User "{u.full_name}" {status}.', 'warning')
    return redirect(url_for('admin.users'))


# Bookings
@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=all_bookings)
