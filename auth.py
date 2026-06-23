from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and current_user.is_authenticated:
        logout_user()
        flash('You have been logged out.', 'info')
        return render_template('auth/login.html')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html')

        if user.is_blacklisted:
            flash('Your account has been blacklisted. Contact admin.', 'danger')
            return render_template('auth/login.html')

        if user.role == 'staff' and not user.is_approved:
            flash('Your staff account is pending admin approval.', 'warning')
            return render_template('auth/login.html')

        login_user(user)
        flash(f'Welcome back, {user.full_name}', 'success')
        return _redirect_by_role(user)

    return render_template('auth/login.html')


def _redirect_by_role(user):
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    if user.role == 'staff':
        return redirect(url_for('staff.dashboard'))
    return redirect(url_for('user.dashboard'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
   
    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not all([username, email, full_name, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email, full_name=full_name,
                    phone=phone, role='user', is_approved=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/staff/register', methods=['GET', 'POST'])
def staff_register():
   
    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not all([username, email, full_name, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('auth/staff_register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/staff_register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/staff_register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/staff_register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/staff_register.html')

        staff = User(username=username, email=email, full_name=full_name,
                     phone=phone, role='staff', is_approved=False)
        staff.set_password(password)
        db.session.add(staff)
        db.session.commit()
        flash('Staff registration submitted.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/staff_register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
