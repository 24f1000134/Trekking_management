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
