from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime, date
import bcrypt
import qrcode
import os
import re

from config import Config
from models import db, User, WalletTransaction, Meal, Attendance, RefundRequest

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure QR code folder exists
os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Auto-deactivate meals after their date has passed
@app.before_request
def deactivate_past_meals():
    Meal.query.filter(Meal.date < date.today(), Meal.is_active == True).update({'is_active': False})
    db.session.commit()

# Decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator for student-only routes
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied. Student account required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Helper function to check password
def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# Helper function to generate QR code
def generate_qr_code(roll_number):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(roll_number)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"{roll_number}.png"
    filepath = os.path.join(app.config['QR_CODE_FOLDER'], filename)
    img.save(filepath)
    return f"qr_codes/{filename}"

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password(password, user.password_hash):
            # Check if student account is active
            if user.role == 'student' and not user.is_active:
                flash('Your account has been deactivated. Please contact the administrator.', 'error')
                return render_template('login.html')

            login_user(user)
            flash('Login successful!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_meals_today = Meal.query.filter_by(date=date.today()).count()
    today_attendance = Attendance.query.join(Meal).filter(Meal.date == date.today()).count()
    today_revenue = db.session.query(db.func.sum(Attendance.amount_paid)).join(Meal).filter(Meal.date == date.today()).scalar() or 0

    recent_attendance = Attendance.query.order_by(Attendance.scanned_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_meals_today=total_meals_today,
                         today_attendance=today_attendance,
                         today_revenue=today_revenue,
                         recent_attendance=recent_attendance)

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    return render_template('admin/settings.html')

@app.route('/admin/change-password', methods=['POST'])
@login_required
@admin_required
def admin_change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password(current_password, current_user.password_hash):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('admin_settings'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('admin_settings'))

    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('admin_settings'))

    current_user.password_hash = hash_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/admin/register-student', methods=['GET', 'POST'])
@login_required
@admin_required
def register_student():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_number = request.form.get('roll_number')
        room_number = request.form.get('room_number')
        password = request.form.get('password')
        initial_balance = float(request.form.get('initial_balance', 0))

        # Validate roll number format (YYYY-DEPT-XXX)
        roll_pattern = r'^\d{4}-[A-Za-z]{2,5}-\d{1,4}$'
        if not re.match(roll_pattern, roll_number):
            flash('Invalid roll number format. Use format: YYYY-DEPT-XXX (e.g., 2024-CS-562)', 'error')
            return redirect(url_for('register_student'))

        # Convert to uppercase
        roll_number = roll_number.upper()

        # Check if roll number already exists
        existing_user = User.query.filter_by(username=roll_number).first()
        if existing_user:
            flash('Roll number already registered.', 'error')
            return redirect(url_for('register_student'))

        # Generate QR code
        qr_path = generate_qr_code(roll_number)

        # Create user
        new_user = User(
            username=roll_number,
            password_hash=hash_password(password),
            name=name,
            role='student',
            room_number=room_number,
            wallet_balance=initial_balance,
            qr_code_path=qr_path
        )

        db.session.add(new_user)
        db.session.commit()

        # Add initial wallet transaction if balance > 0
        if initial_balance > 0:
            transaction = WalletTransaction(
                user_id=new_user.id,
                amount=initial_balance,
                transaction_type='credit',
                description='Initial wallet balance',
                balance_after=initial_balance
            )
            db.session.add(transaction)
            db.session.commit()

        flash(f'Student {name} registered successfully!', 'success')
        return redirect(url_for('register_student'))

    return render_template('admin/register_student.html')

@app.route('/admin/students')
@login_required
@admin_required
def list_students():
    status_filter = request.args.get('status', 'active')

    if status_filter == 'all':
        students = User.query.filter_by(role='student').order_by(User.name).all()
    elif status_filter == 'inactive':
        students = User.query.filter_by(role='student', is_active=False).order_by(User.name).all()
    else:  # active (default)
        students = User.query.filter_by(role='student', is_active=True).order_by(User.name).all()

    return render_template('admin/students.html', students=students, status_filter=status_filter)

@app.route('/admin/edit-student/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = User.query.get_or_404(student_id)

    if student.role != 'student':
        flash('Invalid student.', 'error')
        return redirect(url_for('list_students'))

    if request.method == 'POST':
        name = request.form.get('name')
        room_number = request.form.get('room_number')
        new_password = request.form.get('password')

        student.name = name
        student.room_number = room_number

        if new_password:
            student.password_hash = hash_password(new_password)

        db.session.commit()
        flash(f'Student {name} updated successfully!', 'success')
        return redirect(url_for('list_students'))

    return render_template('admin/edit_student.html', student=student)

@app.route('/admin/delete-student/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = User.query.get_or_404(student_id)

    if student.role != 'student':
        return jsonify({'success': False, 'message': 'Invalid student'})

    # Soft delete - mark as inactive instead of deleting
    student.is_active = False
    db.session.commit()

    return jsonify({'success': True, 'message': f'Student {student.name} has been deactivated'})

@app.route('/admin/toggle-student-status/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def toggle_student_status(student_id):
    student = User.query.get_or_404(student_id)

    if student.role != 'student':
        return jsonify({'success': False, 'message': 'Invalid student'})

    student.is_active = not student.is_active
    db.session.commit()

    status = 'activated' if student.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'Student {student.name} has been {status}', 'is_active': student.is_active})

@app.route('/admin/add-balance', methods=['GET', 'POST'])
@login_required
@admin_required
def add_balance():
    students = User.query.filter_by(role='student', is_active=True).order_by(User.name).all()

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        amount = float(request.form.get('amount'))

        student = User.query.get(student_id)
        if student:
            student.wallet_balance += amount

            transaction = WalletTransaction(
                user_id=student.id,
                amount=amount,
                transaction_type='credit',
                description='Balance added by admin',
                balance_after=student.wallet_balance
            )
            db.session.add(transaction)
            db.session.commit()

            flash(f'Added Rs. {amount} to {student.name}\'s wallet.', 'success')
        else:
            flash('Student not found.', 'error')

        return redirect(url_for('add_balance'))

    return render_template('admin/wallet.html', students=students)

@app.route('/admin/meals', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_meals():
    if request.method == 'POST':
        meal_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        meal_type = request.form.get('meal_type')
        price = float(request.form.get('price'))
        menu_items = request.form.get('menu_items', '').strip()

        # Check if meal already exists
        existing_meal = Meal.query.filter_by(date=meal_date, meal_type=meal_type).first()
        if existing_meal:
            flash('This meal already exists for the selected date.', 'error')
        else:
            new_meal = Meal(
                date=meal_date,
                meal_type=meal_type,
                price=price,
                menu_items=menu_items if menu_items else None
            )
            db.session.add(new_meal)
            db.session.commit()
            flash('Meal added successfully!', 'success')

        return redirect(url_for('manage_meals'))

    meals = Meal.query.order_by(Meal.date.desc(), Meal.meal_type).limit(50).all()
    return render_template('admin/meals.html', meals=meals, today=date.today().isoformat())

@app.route('/admin/edit-meal/<int:meal_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)

    if request.method == 'POST':
        meal_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        meal_type = request.form.get('meal_type')
        price = float(request.form.get('price'))
        menu_items = request.form.get('menu_items', '').strip()
        is_active = request.form.get('is_active') == 'on'

        # Check if another meal exists with same date and type
        existing_meal = Meal.query.filter(
            Meal.date == meal_date,
            Meal.meal_type == meal_type,
            Meal.id != meal_id
        ).first()

        if existing_meal:
            flash('Another meal already exists for this date and type.', 'error')
        else:
            meal.date = meal_date
            meal.meal_type = meal_type
            meal.price = price
            meal.menu_items = menu_items if menu_items else None
            meal.is_active = is_active
            db.session.commit()
            flash('Meal updated successfully!', 'success')
            return redirect(url_for('manage_meals'))

    return render_template('admin/edit_meal.html', meal=meal)

@app.route('/admin/scan')
@login_required
@admin_required
def scan_qr():
    today_meals = Meal.query.filter_by(date=date.today(), is_active=True).all()
    return render_template('admin/scan.html', meals=today_meals)

@app.route('/admin/process-scan', methods=['POST'])
@login_required
@admin_required
def process_scan():
    data = request.get_json()
    roll_number = data.get('roll_number')
    meal_id = data.get('meal_id')

    # Find student
    student = User.query.filter_by(username=roll_number, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'})

    # Check if student is active
    if not student.is_active:
        return jsonify({'success': False, 'message': 'Student account is deactivated.'})

    # Find meal
    meal = Meal.query.get(meal_id)
    if not meal:
        return jsonify({'success': False, 'message': 'Meal not found.'})

    # Check if already attended
    existing_attendance = Attendance.query.filter_by(user_id=student.id, meal_id=meal.id).first()
    if existing_attendance:
        return jsonify({'success': False, 'message': f'{student.name} has already scanned for this meal.'})

    # Check wallet balance
    if student.wallet_balance < meal.price:
        return jsonify({'success': False, 'message': f'Insufficient balance. Current balance: Rs. {student.wallet_balance}'})

    # Deduct balance
    student.wallet_balance -= meal.price

    # Record transaction
    transaction = WalletTransaction(
        user_id=student.id,
        amount=-meal.price,
        transaction_type='debit',
        description=f'{meal.meal_type.capitalize()} on {meal.date}',
        balance_after=student.wallet_balance
    )
    db.session.add(transaction)

    # Record attendance
    attendance = Attendance(
        user_id=student.id,
        meal_id=meal.id,
        amount_paid=meal.price
    )
    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Success! {student.name} - {meal.meal_type.capitalize()}',
        'student_name': student.name,
        'meal_type': meal.meal_type,
        'amount': meal.price,
        'new_balance': student.wallet_balance
    })

@app.route('/admin/reports')
@login_required
@admin_required
def reports():
    # Get date range from query params
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Attendance report
    attendance_data = db.session.query(
        Meal.date,
        Meal.meal_type,
        db.func.count(Attendance.id).label('count'),
        db.func.sum(Attendance.amount_paid).label('revenue')
    ).join(Attendance).filter(
        Meal.date >= start,
        Meal.date <= end
    ).group_by(Meal.date, Meal.meal_type).order_by(Meal.date.desc()).all()

    # Total revenue
    total_revenue = db.session.query(
        db.func.sum(Attendance.amount_paid)
    ).join(Meal).filter(
        Meal.date >= start,
        Meal.date <= end
    ).scalar() or 0

    # Total attendance
    total_attendance = db.session.query(
        db.func.count(Attendance.id)
    ).join(Meal).filter(
        Meal.date >= start,
        Meal.date <= end
    ).scalar() or 0

    return render_template('admin/reports.html',
                         attendance_data=attendance_data,
                         total_revenue=total_revenue,
                         total_attendance=total_attendance,
                         start_date=start_date,
                         end_date=end_date)

# ==================== STUDENT ROUTES ====================

@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    today_meals = Meal.query.filter_by(date=date.today(), is_active=True).all()
    recent_transactions = WalletTransaction.query.filter_by(user_id=current_user.id)\
        .order_by(WalletTransaction.created_at.desc()).limit(5).all()

    return render_template('student/dashboard.html',
                         today_meals=today_meals,
                         recent_transactions=recent_transactions)

@app.route('/student/profile')
@login_required
@student_required
def student_profile():
    return render_template('student/profile.html')

@app.route('/student/change-password', methods=['POST'])
@login_required
@student_required
def student_change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password(current_password, current_user.password_hash):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('student_profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('student_profile'))

    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'error')
        return redirect(url_for('student_profile'))

    current_user.password_hash = hash_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('student_profile'))

@app.route('/student/wallet')
@login_required
@student_required
def student_wallet():
    transactions = WalletTransaction.query.filter_by(user_id=current_user.id)\
        .order_by(WalletTransaction.created_at.desc()).all()
    return render_template('student/wallet.html', transactions=transactions)

@app.route('/student/attendance')
@login_required
@student_required
def student_attendance():
    attendances = Attendance.query.filter_by(user_id=current_user.id)\
        .order_by(Attendance.scanned_at.desc()).all()
    return render_template('student/attendance.html', attendances=attendances)

@app.route('/student/meals')
@login_required
@student_required
def student_meals():
    upcoming_meals = Meal.query.filter(
        Meal.date >= date.today(),
        Meal.is_active == True
    ).order_by(Meal.date, Meal.meal_type).all()
    return render_template('student/meals.html', meals=upcoming_meals, today=date.today())

@app.route('/student/refund-requests')
@login_required
def student_refund_requests():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))

    # Get student's refund requests
    refund_requests = RefundRequest.query.filter_by(user_id=current_user.id).order_by(RefundRequest.created_at.desc()).all()

    # Get recent attendance records that can be refunded (within last 24 hours, no existing refund request)
    from datetime import timedelta
    cutoff_time = datetime.now() - timedelta(hours=24)

    eligible_attendances = db.session.query(Attendance).filter(
        Attendance.user_id == current_user.id,
        Attendance.scanned_at >= cutoff_time
    ).outerjoin(RefundRequest).filter(
        RefundRequest.id == None
    ).order_by(Attendance.scanned_at.desc()).all()

    return render_template('student/refund_requests.html',
                           refund_requests=refund_requests,
                           eligible_attendances=eligible_attendances)

@app.route('/student/request-refund/<int:attendance_id>', methods=['POST'])
@login_required
def request_refund(attendance_id):
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    # Check if attendance belongs to current user
    attendance = Attendance.query.get_or_404(attendance_id)
    if attendance.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})

    # Check if already requested refund for this attendance
    existing_request = RefundRequest.query.filter_by(attendance_id=attendance_id).first()
    if existing_request:
        return jsonify({'success': False, 'message': 'Refund already requested for this meal'})

    # Check if within 24 hours
    from datetime import timedelta
    if datetime.now() - attendance.scanned_at > timedelta(hours=24):
        return jsonify({'success': False, 'message': 'Refund can only be requested within 24 hours of scanning'})

    reason = request.json.get('reason', '')

    # Create refund request
    refund_request = RefundRequest(
        user_id=current_user.id,
        attendance_id=attendance_id,
        amount=attendance.amount_paid,
        reason=reason
    )
    db.session.add(refund_request)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Refund request submitted successfully'})

# ==================== ADMIN REFUND MANAGEMENT ====================

@app.route('/admin/refund-requests')
@login_required
@admin_required
def admin_refund_requests():
    pending_requests = RefundRequest.query.filter_by(status='pending').order_by(RefundRequest.created_at.desc()).all()
    processed_requests = RefundRequest.query.filter(RefundRequest.status != 'pending').order_by(RefundRequest.processed_at.desc()).limit(50).all()

    return render_template('admin/refund_requests.html',
                           pending_requests=pending_requests,
                           processed_requests=processed_requests)

@app.route('/admin/process-refund/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def process_refund(request_id):
    refund_request = RefundRequest.query.get_or_404(request_id)

    if refund_request.status != 'pending':
        return jsonify({'success': False, 'message': 'Request already processed'})

    action = request.json.get('action')  # 'approve' or 'reject'
    remarks = request.json.get('remarks', '')

    if action == 'approve':
        # Credit the amount back to student's wallet
        student = refund_request.user
        student.wallet_balance += refund_request.amount

        # Create wallet transaction
        transaction = WalletTransaction(
            user_id=student.id,
            amount=refund_request.amount,
            transaction_type='credit',
            description=f'Refund for {refund_request.attendance.meal.meal_type} on {refund_request.attendance.meal.date}',
            balance_after=student.wallet_balance
        )
        db.session.add(transaction)

        refund_request.status = 'approved'
        refund_request.admin_remarks = remarks
        refund_request.processed_at = datetime.now()

        db.session.commit()
        return jsonify({'success': True, 'message': f'Refund of Rs. {refund_request.amount} approved and credited to student wallet'})

    elif action == 'reject':
        refund_request.status = 'rejected'
        refund_request.admin_remarks = remarks
        refund_request.processed_at = datetime.now()

        db.session.commit()
        return jsonify({'success': True, 'message': 'Refund request rejected'})

    return jsonify({'success': False, 'message': 'Invalid action'})

# ==================== API ENDPOINTS ====================

@app.route('/api/check-roll-number')
@login_required
@admin_required
def check_roll_number():
    roll = request.args.get('roll', '')
    exists = User.query.filter_by(username=roll).first() is not None
    return jsonify({'exists': exists})

@app.route('/api/students/search')
@login_required
@admin_required
def search_students():
    query = request.args.get('q', '')
    students = User.query.filter(
        User.role == 'student',
        db.or_(
            User.name.ilike(f'%{query}%'),
            User.username.ilike(f'%{query}%'),
            User.room_number.ilike(f'%{query}%')
        )
    ).order_by(User.name).limit(20).all()

    return jsonify([{
        'id': s.id,
        'name': s.name,
        'username': s.username,
        'room_number': s.room_number,
        'wallet_balance': s.wallet_balance
    } for s in students])

@app.route('/api/students/<int:student_id>')
@login_required
@admin_required
def get_student(student_id):
    student = User.query.get_or_404(student_id)
    total_meals = Attendance.query.filter_by(user_id=student.id).count()

    return jsonify({
        'id': student.id,
        'name': student.name,
        'username': student.username,
        'room_number': student.room_number,
        'wallet_balance': student.wallet_balance,
        'qr_code_path': student.qr_code_path,
        'total_meals': total_meals,
        'created_at': student.created_at.isoformat()
    })

@app.route('/api/students/add-balance', methods=['POST'])
@login_required
@admin_required
def api_add_balance():
    data = request.get_json()
    student_id = data.get('student_id')
    amount = float(data.get('amount', 0))

    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'})

    student = User.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'})

    student.wallet_balance += amount

    transaction = WalletTransaction(
        user_id=student.id,
        amount=amount,
        transaction_type='credit',
        description='Balance added by admin',
        balance_after=student.wallet_balance
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Added Rs. {amount} to wallet',
        'new_balance': student.wallet_balance
    })

@app.route('/api/meals/<int:meal_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)

    # Check if meal has attendance records
    attendance_count = Attendance.query.filter_by(meal_id=meal.id).count()
    if attendance_count > 0:
        return jsonify({'success': False, 'message': 'Cannot delete meal with attendance records'})

    db.session.delete(meal)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Meal deleted'})

@app.route('/api/meals/<int:meal_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    data = request.get_json()

    meal.is_active = data.get('is_active', not meal.is_active)
    db.session.commit()

    return jsonify({'success': True, 'is_active': meal.is_active})

@app.route('/api/stats/dashboard')
@login_required
@admin_required
def dashboard_stats():
    total_students = User.query.filter_by(role='student').count()
    today_attendance = Attendance.query.join(Meal).filter(Meal.date == date.today()).count()
    today_revenue = db.session.query(
        db.func.sum(Attendance.amount_paid)
    ).join(Meal).filter(Meal.date == date.today()).scalar() or 0

    return jsonify({
        'total_students': total_students,
        'today_attendance': today_attendance,
        'today_revenue': today_revenue
    })

@app.route('/api/stats/meal-attendance')
@login_required
@admin_required
def meal_attendance_stats():
    # Get today's attendance by meal type
    stats = db.session.query(
        Meal.meal_type,
        db.func.count(Attendance.id)
    ).join(Attendance).filter(
        Meal.date == date.today()
    ).group_by(Meal.meal_type).all()

    result = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
    for meal_type, count in stats:
        result[meal_type] = count

    return jsonify(result)

@app.route('/api/stats/revenue')
@login_required
@admin_required
def revenue_stats():
    from datetime import timedelta

    # Get last 7 days revenue
    labels = []
    values = []

    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        revenue = db.session.query(
            db.func.sum(Attendance.amount_paid)
        ).join(Meal).filter(Meal.date == day).scalar() or 0

        labels.append(day.strftime('%a'))
        values.append(float(revenue))

    return jsonify({'labels': labels, 'values': values})

@app.route('/api/stats/weekly-trend')
@login_required
@admin_required
def weekly_trend():
    from datetime import timedelta

    labels = []
    values = []

    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        count = Attendance.query.join(Meal).filter(Meal.date == day).count()

        labels.append(day.strftime('%a'))
        values.append(count)

    return jsonify({'labels': labels, 'values': values})

@app.route('/api/reports/export')
@login_required
@admin_required
def export_report():
    import csv
    from io import StringIO
    from flask import Response

    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Get attendance data
    attendance_data = db.session.query(
        Meal.date,
        Meal.meal_type,
        User.name,
        User.username,
        Attendance.amount_paid,
        Attendance.scanned_at
    ).join(Attendance, Meal.id == Attendance.meal_id)\
     .join(User, User.id == Attendance.user_id)\
     .filter(Meal.date >= start, Meal.date <= end)\
     .order_by(Meal.date.desc(), Attendance.scanned_at).all()

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Meal Type', 'Student Name', 'Roll Number', 'Amount', 'Scan Time'])

    for row in attendance_data:
        writer.writerow([
            row.date.strftime('%Y-%m-%d'),
            row.meal_type.capitalize(),
            row.name,
            row.username,
            row.amount_paid,
            row.scanned_at.strftime('%I:%M:%S %p')
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=report_{start_date}_to_{end_date}.csv'}
    )

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
