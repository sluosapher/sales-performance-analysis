from flask import Flask, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta, datetime
import os
import uuid
from pathlib import Path
import tempfile
from werkzeug.utils import secure_filename
import shutil

# Import models
from models import db, User
from forms import LoginForm, PasswordChangeForm, UserForm, UserEditForm, PasswordResetForm, TokenRegenerateForm

# Import sales processing functions from sales_mcp_server
from sales_mcp_server import process_input_file, format_result_file, extract_timestamp_from_stem

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Configure CSRF protection
app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
app.config['WTF_CSRF_ENABLED'] = True

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info' # Changed to info for better user experience

ALLOWED_EXTENSIONS = {"xlsx"}

def allowed_file(filename):
    """Check if file has allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

from forms import UploadForm

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Permission Decorators ---
def require_upload_permission(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        if not current_user.can_upload:
            flash('You do not have permission to upload files.', 'warning')
            return redirect(url_for('error', error_title='Access Denied', error_message='You do not have permission to upload files.'))
        return f(*args, **kwargs)
    return decorated_function

def require_list_permission(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        if not current_user.can_list_results:
            flash('You do not have permission to view results.', 'warning')
            return redirect(url_for('error', error_title='Access Denied', error_message='You do not have permission to view results.'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        if current_user.role != 'admin':
            flash('You do not have administrative privileges.', 'danger')
            abort(403) # Or redirect to an unauthorized page
        return f(*args, **kwargs)
    return decorated_function

# --- Core Routes ---
@app.route('/')
def index():
    """Home page redirect based on permissions"""
    if current_user.is_authenticated:
        if current_user.can_upload:
            return redirect(url_for('upload_file'))
        elif current_user.can_list_results:
            return redirect(url_for('list_results'))
        else:
            return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow() # Use datetime.utcnow() for consistency
            db.session.commit()

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.can_upload:
                return redirect(url_for('upload_file'))
            elif user.can_list_results:
                return redirect(url_for('list_results'))
            else:
                return redirect(url_for('profile'))

        flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form, title='Login')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with token display and password change"""
    password_form = PasswordChangeForm()
    token_form = TokenRegenerateForm()

    if password_form.validate_on_submit():
        if check_password_hash(current_user.password_hash, password_form.current_password.data):
            current_user.password_hash = generate_password_hash(password_form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect', 'danger')

    if token_form.validate_on_submit():
        current_user.generate_token()
        db.session.commit()
        flash('Token regenerated successfully', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html',
                         title='Profile',
                         password_form=password_form,
                         token_form=token_form)

# --- Admin Routes ---
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """List all users"""
    users = User.query.all()
    return render_template('admin_users.html', users=users, title='User Management')

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    """Add new user"""
    form = UserForm()
    if form.validate_on_submit():
        # Generate token
        token = str(uuid.uuid4())

        user = User(
            username=form.username.data,
            password_hash=bcrypt.generate_password_hash(form.password.data).decode('utf-8'),
            role=form.role.data,
            can_upload=form.can_upload.data,
            can_list_results=form.can_list_results.data,
            secret_token=token
        )

        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created successfully', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_user_form.html', form=form, title='Add User')

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Edit user"""
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        user.can_upload = form.can_upload.data
        user.can_list_results = form.can_list_results.data

        db.session.commit()
        flash(f'User {user.username} updated successfully', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_user_form.html', form=form, user=user, title='Edit User')

@app.route('/admin/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete user"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted successfully', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_delete_user.html', user=user, title='Delete User')

@app.route('/admin/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Reset user password"""
    user = User.query.get_or_404(user_id)
    form = PasswordResetForm()

    if form.validate_on_submit():
        user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.commit()
        flash(f'Password reset for {user.username}', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_reset_password.html', form=form, user=user, title='Reset Password')

@app.route('/admin/users/<int:user_id>/regenerate-token', methods=['POST'])
@login_required
@admin_required
def admin_regenerate_token(user_id):
    """Regenerate user token"""
    user = User.query.get_or_404(user_id)
    user.generate_token()
    db.session.commit()
    flash(f'Token regenerated for {user.username}', 'success')
    return redirect(url_for('admin_users'))

# --- Error Route ---
@app.route('/error')
def error():
    """Generic error page"""
    error_title = request.args.get('error_title', 'Error')
    error_message = request.args.get('error_message', 'An unexpected error occurred.')
    return render_template('error.html', error_title=error_title, error_message=error_message)

# --- Sales Analysis Web Routes (integrated from web_routes.py) ---
@app.route("/upload", methods=["GET", "POST"])
@login_required
@require_upload_permission
def upload_file():
    """Handle file upload and processing."""
    form = UploadForm()

    if request.method == "GET":
        return render_template("upload.html", form=form)

    if form.validate_on_submit():
        if "file" not in request.files:
            flash("No file part in the request", 'danger')
            return redirect(url_for('error', error_title="No File Selected", error_message="Please select a file to upload."))

        file = request.files["file"]
    if file.filename == "":
        flash("No selected file", 'danger')
        return redirect(url_for('error', error_title="No File Selected", error_message="Please select a file to upload."))

    if file and allowed_file(file.filename):
        # Validate filename pattern
        if not extract_timestamp_from_stem(file.filename.replace(".xlsx", "")):
            flash(f"Filename must match pattern: raw_data_YYMMDD.xlsx. Got: {file.filename}", 'danger')
            return redirect(url_for('error', error_title="Invalid Filename", error_message=f"Filename must match pattern: raw_data_YYMMDD.xlsx. Got: {file.filename}"))

        try:
            # Save uploaded file to temporary location
            temp_dir = Path(tempfile.mkdtemp())
            input_path = temp_dir / secure_filename(file.filename)
            file.save(str(input_path))

            # Process the file
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path, timestamp = process_input_file(input_path, output_dir)

            # Format results
            results_text = format_result_file(output_path)

            generation_date = datetime.now().strftime("%Y-%m-%d")

            flash('File processed successfully!', 'success')
            return render_template(
                "results.html",
                filename=file.filename,
                timestamp=timestamp,
                generated_date=generation_date,
                results_text=results_text,
                result_filename=output_path.name,
            )

        except ValueError as e:
            flash(f"Failed to process file: {str(e)}", 'danger')
            return redirect(url_for('error', error_title="Processing Error", error_message=f"Failed to process file: {e}"))

        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", 'danger')
            return redirect(url_for('error', error_title="Unexpected Error", error_message=f"An unexpected error occurred: {e}"))

        finally:
            if "temp_dir" in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        flash("Please upload an Excel file (.xlsx) with the correct filename pattern (raw_data_YYMMDD.xlsx).", 'danger')
        return redirect(url_for('error', error_title="Invalid File Type", error_message="Please upload an Excel file (.xlsx) with the correct filename pattern (raw_data_YYMMDD.xlsx)."))

@app.route("/list-results")
@login_required
@require_list_permission
def list_results():
    """List all available result files and allow viewing/downloading."""
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    result_files = sorted(output_dir.glob("result_*.xlsx"), key=os.path.getmtime, reverse=True)

    files_info = []
    for file_path in result_files:
        stat = file_path.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_kb = stat.st_size / 1024
        files_info.append({
            'name': file_path.name,
            'modified': mod_time,
            'size': f"{size_kb:.1f} KB",
            'download_url': url_for('download_file', filename=file_path.name),
            'view_url': url_for('view_result', filename=file_path.name)
        })
    return render_template('list_results.html', files=files_info, title='Available Result Files')

@app.route("/view-result/<string:filename>")
@login_required
@require_list_permission
def view_result(filename):
    """View formatted results from a specific result file."""
    output_dir = Path("output")
    result_path = output_dir / filename

    if not result_path.exists():
        flash(f"File {filename} not found.", 'danger')
        return redirect(url_for('error', error_title="File Not Found", error_message=f"File {filename} not found."))

    try:
        result_text = format_result_file(result_path)
        return render_template('view_result.html', filename=filename, results_text=result_text, title=f'View Result: {filename}')
    except Exception as e:
        flash(f"Error: Failed to format result: {e}", 'danger')
        return redirect(url_for('error', error_title="Formatting Error", error_message=f"Failed to format result: {e}"))

@app.route("/download/<path:filename>")
@login_required
def download_file(filename):
    """Download the generated Excel report."""
    output_dir = Path("output")
    output_path = output_dir / filename

    if output_path.exists():
        return send_file(str(output_path), as_attachment=True)
    else:
        flash(f"File {filename} not found.", 'danger')
        return redirect(url_for('error', error_title="File Not Found", error_message="The requested file could not be found."))

if __name__ == '__main__':
    import threading
    import time
    from sales_mcp_server import mcp_app

    # Start MCP server in a separate thread
    def run_mcp_server():
        print("Starting MCP server on port 8003...")
        # A small delay to allow the main Flask app to fully initialize its context
        # before the MCP app tries to access it via db.init_app(app) or app.app_context()
        time.sleep(1)
        with app.app_context(): # Ensure MCP app runs within the Flask app's context for DB access
            mcp_app.run(transport="http", host="0.0.0.0", port=8003)

    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # Start Flask web server in the main thread
    print("Starting web interface on port 8004...")
    app.run(host='0.0.0.0', port=8004, debug=True)
