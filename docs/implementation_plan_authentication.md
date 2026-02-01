# Authentication Implementation Plan

**Date:** 2026-02-01
**Project:** Sales Performance Analysis - Authentication System

## Overview

This document provides a step-by-step implementation plan for adding username/password authentication with role-based permissions to the sales performance analysis system. The implementation will modify existing web routes and integrate with the MCP server for token-based authentication.

---

## Phase 1: Environment Setup & Dependencies

### Step 1.1: Install Dependencies

Install the required Flask extensions and database packages:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install authentication dependencies
uv add Flask-Login Flask-Bcrypt Flask-WTF Flask-SQLAlchemy SQLAlchemy

# Verify installations
uv run pip list | grep -E "(Flask-Login|Flask-Bcrypt|Flask-WTF|Flask-SQLAlchemy|SQLAlchemy)"
```

**Expected Dependencies:**
- Flask-Login >= 0.6.0
- Flask-Bcrypt >= 1.0.0
- Flask-WTF >= 1.0.0
- Flask-SQLAlchemy >= 3.0.0
- SQLAlchemy >= 2.0.0
- Werkzeug >= 2.0.0

### Step 1.2: Create Project Structure

Create necessary directories:

```bash
# Create templates directory structure
mkdir -p templates/auth
mkdir -p templates/admin
mkdir -p templates/errors

# Create data directory (gitignored)
mkdir -p data

# Create static directory for CSS/JS
mkdir -p static/css
mkdir -p static/js
```

**Directory Structure:**
```
sales-performance-analysis/
├── data/
│   └── users.db              # SQLite database (created automatically)
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── access_denied.html
│   ├── admin/
│   │   ├── users.html
│   │   ├── user_form.html
│   │   └── confirm_delete.html
│   └── profile.html
├── static/
│   ├── css/
│   └── js/
└── (existing files...)
```

---

## Phase 2: Database Models & Configuration

### Step 2.1: Create Database Models

Create `models.py` in the project root:

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\models.py`**

```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model with authentication and permissions"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    secret_token = db.Column(db.String(36), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    can_upload = db.Column(db.Boolean, default=False, nullable=False)
    can_list_results = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    force_password_change = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='bcrypt', rounds=12)

    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        """Generate a new secret token"""
        self.secret_token = str(uuid.uuid4())
        return self.secret_token

    def regenerate_token(self):
        """Regenerate secret token"""
        return self.generate_token()

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.role == 'admin':
            return True
        if permission == 'upload':
            return self.can_upload
        elif permission == 'list_results':
            return self.can_list_results
        return False

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'can_upload': self.can_upload,
            'can_list_results': self.can_list_results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'force_password_change': self.force_password_change,
        }
        if include_sensitive:
            data['secret_token'] = self.secret_token
        return data

    def __repr__(self):
        return f'<User {self.username}>'

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)

def create_db(app):
    """Create database tables"""
    with app.app_context():
        db.create_all()

def get_user_by_token(token: str) -> User | None:
    """Get user by secret token"""
    if not token:
        return None
    return User.query.filter_by(secret_token=token).first()

def create_default_users(app):
    """Create default admin and test users"""
    with app.app_context():
        # Check if users already exist
        if User.query.count() > 0:
            return

        # Create admin user
        admin = User(
            username='admin',
            role='admin',
            can_upload=True,
            can_list_results=True,
            force_password_change=True
        )
        admin.set_password('admin123')
        admin.generate_token()
        db.session.add(admin)

        # Create regular user (list only)
        regular_user = User(
            username='user',
            role='user',
            can_upload=False,
            can_list_results=True,
            force_password_change=True
        )
        regular_user.set_password('user123')
        regular_user.generate_token()
        db.session.add(regular_user)

        # Create uploader user
        uploader = User(
            username='uploader',
            role='user',
            can_upload=True,
            can_list_results=True,
            force_password_change=True
        )
        uploader.set_password('upload123')
        uploader.generate_token()
        db.session.add(uploader)

        db.session.commit()
        print("Default users created successfully!")
        print("Admin credentials: admin / admin123")
        print("User credentials: user / user123")
        print("Uploader credentials: uploader / upload123")
```

### Step 2.2: Update Configuration

Add database configuration to `web_routes.py` (at the top after imports):

```python
# Add after existing imports
from models import db, init_db, create_db, get_user_by_token, User, create_default_users
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, CSRFError
from datetime import timedelta

# Initialize extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

# Add configuration in app initialization
def create_app():
    app = Flask(__name__)

    # Existing config...
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_SECURE'] = False

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'warning'

    # Create database and default users
    with app.app_context():
        create_db(app)
        create_default_users(app)

    return app
```

### Step 2.3: Update Login Manager

Add user loader function:

```python
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))
```

---

## Phase 3: Authentication System

### Step 3.1: Create Authentication Decorators

Add to `web_routes.py` after the login_manager configuration:

```python
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if current_user.role != 'admin':
            flash('Administrator access required.', 'error')
            return redirect(url_for('access_denied'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if not current_user.has_permission(permission):
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('access_denied'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def update_last_login(f):
    """Decorator to update last_login timestamp"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            current_user.last_login = datetime.utcnow()
            db.session.commit()
        return f(*args, **kwargs)
    return decorated_function
```

### Step 3.2: Create Login Route

Add login route to `web_routes.py`:

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect_after_login()

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            # Check if password needs to be changed
            if user.force_password_change:
                login_user(user, remember=form.remember_me.data)
                flash('Please change your password.', 'warning')
                return redirect(url_for('profile'))

            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash('Login successful!', 'success')
            return redirect_after_login()

        flash('Invalid username or password', 'error')

    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def redirect_after_login():
    """Redirect user based on permissions"""
    if current_user.can_upload:
        return redirect(url_for('upload'))
    elif current_user.can_list_results:
        return redirect(url_for('list_results'))
    else:
        flash('You do not have any active permissions. Contact administrator.', 'error')
        return redirect(url_for('profile'))
```

### Step 3.3: Create Login Form

Create `forms.py` in project root:

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\forms.py`**

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember_me = BooleanField('Remember me for 30 days')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

    def validate_current_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError('Current password is incorrect')

class UserForm(FlaskForm):
    """Create/edit user form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    can_upload = BooleanField('Can Upload Files')
    can_list_results = BooleanField('Can List Results')
    force_password_change = BooleanField('Force Password Change on Next Login')
    submit = SubmitField('Create User')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Username already exists')

class EditUserForm(FlaskForm):
    """Edit user form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    can_upload = BooleanField('Can Upload Files')
    can_list_results = BooleanField('Can List Results')
    force_password_change = BooleanField('Force Password Change on Next Login')
    submit = SubmitField('Update User')

    def __init__(self, original_username, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, field):
        if field.data != self.original_username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Username already exists')
```

Add to top of forms.py:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_login import current_user
from models import User
```

---

## Phase 4: Templates & Pages

### Step 4.1: Create Base Template

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sales Performance Analysis{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Custom CSS -->
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">

    {% block head %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    {% if current_user.is_authenticated %}
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('upload') }}">
                Sales Analysis Portal
            </a>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    {% if current_user.can_upload %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('upload') }}">Upload Files</a>
                    </li>
                    {% endif %}

                    {% if current_user.can_list_results %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('list_results') }}">List Results</a>
                    </li>
                    {% endif %}

                    {% if current_user.role == 'admin' %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('admin_users') }}">Admin</a>
                    </li>
                    {% endif %}
                </ul>

                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('profile') }}">Profile</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    {% endif %}

    <!-- Flash Messages -->
    <div class="container mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <!-- Main Content -->
    <div class="container {% if not current_user.is_authenticated %}mt-5{% endif %}">
        {% block content %}{% endblock %}
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Clipboard JS -->
    <script>
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;

            navigator.clipboard.writeText(text).then(() => {
                alert('Token copied to clipboard!');
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        }
    </script>

    {% block scripts %}{% endblock %}
</body>
</html>
```

### Step 4.2: Create Login Template

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\auth\login.html`**

```html
{% extends "base.html" %}

{% block title %}Login - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card shadow">
            <div class="card-body">
                <h2 class="card-title text-center mb-4">Sign In</h2>

                <form method="POST" action="{{ url_for('login') }}">
                    {{ form.hidden_tag() }}

                    <div class="mb-3">
                        {{ form.username.label(class="form-label") }}
                        {{ form.username(class="form-control", placeholder="Enter username") }}
                        {% for error in form.username.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control", placeholder="Enter password") }}
                        {% for error in form.password.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="mb-3 form-check">
                        {{ form.remember_me(class="form-check-input") }}
                        {{ form.remember_me.label(class="form-check-label") }}
                    </div>

                    <div class="d-grid">
                        {{ form.submit(class="btn btn-primary") }}
                    </div>
                </form>

                <div class="mt-3 text-center">
                    <small class="text-muted">
                        Default credentials:<br>
                        <strong>admin</strong> / admin123<br>
                        <strong>user</strong> / user123<br>
                        <strong>uploader</strong> / upload123
                    </small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 4.3: Create Access Denied Template

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\auth\access_denied.html`**

```html
{% extends "base.html" %}

{% block title %}Access Denied - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-body text-center">
                <h1 class="display-1">403</h1>
                <h2 class="mb-3">Access Denied</h2>
                <p class="lead">You do not have permission to access this page.</p>

                {% if current_user.is_authenticated %}
                    <p>
                        Your account: <strong>{{ current_user.username }}</strong><br>
                        Role: <strong>{{ current_user.role }}</strong><br>
                        Upload Permission: <strong>{{ 'Yes' if current_user.can_upload else 'No' }}</strong><br>
                        List Permission: <strong>{{ 'Yes' if current_user.can_list_results else 'No' }}</strong>
                    </p>
                    <a href="{{ url_for('profile') }}" class="btn btn-primary">View Profile</a>
                {% endif %}

                {% if current_user.role == 'admin' %}
                    <a href="{{ url_for('admin_users') }}" class="btn btn-secondary">Manage Users</a>
                {% endif %}

                <a href="{{ url_for('logout') }}" class="btn btn-outline-danger">Logout</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 4.4: Create Profile Template

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\profile.html`**

```html
{% extends "base.html" %}

{% block title %}Profile - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <div class="card mb-4">
            <div class="card-header">
                <h3>User Profile</h3>
            </div>
            <div class="card-body">
                <table class="table">
                    <tr>
                        <th>Username:</th>
                        <td>{{ current_user.username }}</td>
                    </tr>
                    <tr>
                        <th>Role:</th>
                        <td>
                            <span class="badge {% if current_user.role == 'admin' %}bg-danger{% else %}bg-info{% endif %}">
                                {{ current_user.role|capitalize }}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <th>Upload Permission:</th>
                        <td>{{ 'Yes' if current_user.can_upload else 'No' }}</td>
                    </tr>
                    <tr>
                        <th>List Results Permission:</th>
                        <td>{{ 'Yes' if current_user.can_list_results else 'No' }}</td>
                    </tr>
                    <tr>
                        <th>Created:</th>
                        <td>{{ current_user.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                    </tr>
                    <tr>
                        <th>Last Login:</th>
                        <td>{{ current_user.last_login.strftime('%Y-%m-%d %H:%M') if current_user.last_login else 'Never' }}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="card mb-4">
            <div class="card-header">
                <h3>Secret Token</h3>
            </div>
            <div class="card-body">
                <p>Use this token for MCP tool authentication:</p>
                <div class="input-group">
                    <input type="text" class="form-control" id="user-token"
                           value="{{ current_user.secret_token }}" readonly>
                    <button class="btn btn-outline-secondary" type="button"
                            onclick="copyToClipboard('user-token')">
                        Copy
                    </button>
                </div>
                <small class="text-muted">
                    This token is unique to your account. Keep it secure and do not share it.
                </small>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3>Change Password</h3>
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('change_password') }}">
                    {{ form.hidden_tag() }}

                    <div class="mb-3">
                        {{ form.current_password.label(class="form-label") }}
                        {{ form.current_password(class="form-control") }}
                        {% for error in form.current_password.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        {{ form.new_password.label(class="form-label") }}
                        {{ form.new_password(class="form-control") }}
                        {% for error in form.new_password.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        {{ form.confirm_password.label(class="form-label") }}
                        {{ form.confirm_password(class="form-control") }}
                        {% for error in form.confirm_password.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="d-grid">
                        {{ form.submit(class="btn btn-primary") }}
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 4.5: Create Custom CSS

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\static\css\style.css`**

```css
body {
    background-color: #f8f9fa;
}

.card {
    border-radius: 10px;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar-brand {
    font-weight: bold;
}

.btn {
    border-radius: 5px;
}

.form-control, .form-select {
    border-radius: 5px;
}

.table th {
    border-top: none;
    font-weight: 600;
    color: #495057;
}

.badge {
    font-size: 0.85em;
    padding: 0.35em 0.65em;
}

.alert {
    border-radius: 5px;
    border: none;
}

.alert-dismissible .btn-close {
    padding: 0.75rem 1rem;
}
```

---

## Phase 5: Admin Interface

### Step 5.1: Create Admin Routes

Add admin routes to `web_routes.py`:

```python
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """List all users - admin only"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    """Add new user - admin only"""
    form = UserForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            role=form.role.data,
            can_upload=form.can_upload.data,
            can_list_results=form.can_list_results.data,
            force_password_change=form.force_password_change.data
        )
        user.set_password(form.password.data)
        user.generate_token()
        db.session.add(user)
        db.session.commit()

        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/user_form.html', form=form, title='Add User')

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Edit user - admin only"""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(user.username)

    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        user.can_upload = form.can_upload.data
        user.can_list_results = form.can_list_results.data
        user.force_password_change = form.force_password_change.data
        db.session.commit()

        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    # Populate form with current values
    form.username.data = user.username
    form.role.data = user.role
    form.can_upload.data = user.can_upload
    form.can_list_results.data = user.can_list_results
    form.force_password_change.data = user.force_password_change

    return render_template('admin/user_form.html', form=form, title='Edit User')

@app.route('/admin/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete user - admin only"""
    user = User.query.get_or_404(user_id)

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/confirm_delete.html', user=user)

@app.route('/admin/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Reset user password - admin only"""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        temp_password = 'changeme123'
        user.set_password(temp_password)
        user.force_password_change = True
        db.session.commit()

        flash(f'Password reset for {user.username}. Temporary password: {temp_password}', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/confirm_reset.html', user=user)

@app.route('/admin/users/<int:user_id>/regenerate-token', methods=['POST'])
@login_required
@admin_required
def admin_regenerate_token(user_id):
    """Regenerate user token - admin only"""
    user = User.query.get_or_404(user_id)
    user.regenerate_token()
    db.session.commit()

    flash(f'Token regenerated for {user.username}!', 'success')
    return redirect(url_for('admin_users'))
```

### Step 5.2: Create Admin Templates

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\admin\users.html`**

```html
{% extends "base.html" %}

{% block title %}User Management - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>User Management</h2>
    <a href="{{ url_for('admin_add_user') }}" class="btn btn-primary">Add User</a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Upload</th>
                        <th>List</th>
                        <th>Created</th>
                        <th>Last Login</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.username }}</td>
                        <td>
                            <span class="badge {% if user.role == 'admin' %}bg-danger{% else %}bg-info{% endif %}">
                                {{ user.role|capitalize }}
                            </span>
                        </td>
                        <td>{{ 'Yes' if user.can_upload else 'No' }}</td>
                        <td>{{ 'Yes' if user.can_list_results else 'No' }}</td>
                        <td>{{ user.created_at.strftime('%Y-%m-%d') }}</td>
                        <td>{{ user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never' }}</td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <a href="{{ url_for('admin_edit_user', user_id=user.id) }}"
                                   class="btn btn-outline-primary">Edit</a>
                                <a href="{{ url_for('admin_reset_password', user_id=user.id) }}"
                                   class="btn btn-outline-warning">Reset PW</a>
                                {% if user.id != current_user.id %}
                                <a href="{{ url_for('admin_delete_user', user_id=user.id) }}"
                                   class="btn btn-outline-danger">Delete</a>
                                {% endif %}
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\admin\user_form.html`**

```html
{% extends "base.html" %}

{% block title %}{{ title }} - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h3>{{ title }}</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ form.hidden_tag() }}

                    <div class="mb-3">
                        {{ form.username.label(class="form-label") }}
                        {{ form.username(class="form-control", placeholder="Enter username") }}
                        {% for error in form.username.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    {% if 'password' in form %}
                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control", placeholder="Enter password") }}
                        {% for error in form.password.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        {{ form.confirm_password.label(class="form-label") }}
                        {{ form.confirm_password(class="form-control", placeholder="Confirm password") }}
                        {% for error in form.confirm_password.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}

                    <div class="mb-3">
                        {{ form.role.label(class="form-label") }}
                        {{ form.role(class="form-select") }}
                        {% for error in form.role.errors %}
                            <span class="text-danger">{{ error }}</span>
                        {% endfor %}
                    </div>

                    <div class="mb-3 form-check">
                        {{ form.can_upload(class="form-check-input") }}
                        {{ form.can_upload.label(class="form-check-label") }}
                    </div>

                    <div class="mb-3 form-check">
                        {{ form.can_list_results(class="form-check-input") }}
                        {{ form.can_list_results.label(class="form-check-label") }}
                    </div>

                    <div class="mb-3 form-check">
                        {{ form.force_password_change(class="form-check-input") }}
                        {{ form.force_password_change.label(class="form-check-label") }}
                    </div>

                    <div class="d-grid gap-2">
                        {{ form.submit(class="btn btn-primary") }}
                        <a href="{{ url_for('admin_users') }}" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\admin\confirm_delete.html`**

```html
{% extends "base.html" %}

{% block title %}Delete User - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-danger text-white">
                <h3>Confirm Deletion</h3>
            </div>
            <div class="card-body">
                <p class="lead">Are you sure you want to delete the user <strong>{{ user.username }}</strong>?</p>
                <p class="text-danger">This action cannot be undone!</p>

                <form method="POST">
                    {{ form.hidden_tag() }}
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-danger">Yes, Delete User</button>
                        <a href="{{ url_for('admin_users') }}" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Phase 6: Profile & Password Management

### Step 6.1: Create Profile Route

Add to `web_routes.py`:

```python
@app.route('/profile')
@login_required
@update_last_login
def profile():
    """User profile page"""
    form = ChangePasswordForm()
    return render_template('profile.html', form=form)

@app.route('/profile/change-password', methods=['POST'])
@login_required
@update_last_login
def change_password():
    """Change password"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            current_user.force_password_change = False
            db.session.commit()

            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'error')

    return render_template('profile.html', form=form)
```

---

## Phase 7: MCP Server Integration

### Step 7.1: Update MCP Server Token Verification

Modify `sales_mcp_server.py`:

```python
# Add import at top
from models import get_user_by_token

def verify_authorization() -> tuple[bool, str | None, str]:
    """Verify token and return (is_valid, username, message)"""
    headers = get_http_headers()
    auth = headers.get("authorization") or headers.get("Authorization")

    if not auth:
        return False, None, "No authorization header"

    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
    else:
        token = auth.strip()

    # Check token against database
    user = get_user_by_token(token)
    if user:
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()

        return True, user.username, f"valid token for user: {user.username}"
    else:
        return False, None, "invalid token"
```

---

## Phase 8: Update Existing Web Routes

### Step 8.1: Protect Upload Route

Update the existing `/upload` route in `web_routes.py`:

```python
@app.route('/upload', methods=['GET', 'POST'])
@login_required
@permission_required('upload')
@update_last_login
def upload():
    # ... existing upload code ...
```

### Step 8.2: Protect List Results Route

Update the existing `/list-results` route:

```python
@app.route('/list-results', methods=['GET'])
@login_required
@permission_required('list_results')
@update_last_login
def list_results():
    # ... existing list results code ...
```

### Step 8.3: Protect Download Route

Update or add download route with authentication:

```python
@app.route('/download/<filename>')
@login_required
@update_last_login
def download(filename):
    # ... existing download code ...
```

### Step 8.4: Add Root Route

Add root route that redirects appropriately:

```python
@app.route('/')
def index():
    """Root redirect"""
    if current_user.is_authenticated:
        return redirect_after_login()
    return redirect(url_for('login'))
```

---

## Phase 9: Error Handling

### Step 9.1: Add CSRF Error Handler

Add to `web_routes.py`:

```python
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF token errors"""
    return render_template('errors/csrf_error.html', error=e.description), 400
```

Create template:

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\templates\errors\csrf_error.html`**

```html
{% extends "base.html" %}

{% block title %}CSRF Error - Sales Performance Analysis{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body text-center">
                <h2 class="text-danger">CSRF Token Invalid</h2>
                <p class="lead">Your session has expired or the form is invalid.</p>
                <p>Please try again.</p>
                <a href="{{ url_for('login') }}" class="btn btn-primary">Go to Login</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Phase 10: Database Initialization Script

### Step 10.1: Create Database Setup Script

Create `init_db.py` in project root:

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\init_db.py`**

```python
import os
from app import create_app
from models import db, create_db, create_default_users

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print("Creating database...")
        create_db(app)
        print("Creating default users...")
        create_default_users(app)
        print("Database initialization complete!")
```

---

## Phase 11: Testing & Verification

### Step 11.1: Create Test Users Script

Create `create_test_users.py`:

**File: `C:\Users\sluo_\workspace\sales-performance-analysis\create_test_users.py`**

```python
"""Script to create test users with different permission combinations"""

import sys
from app import create_app
from models import db, User

app = create_app()

def create_users():
    """Create test users"""
    with app.app_context():
        users_data = [
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'can_upload': True,
                'can_list_results': True,
                'force_change': True
            },
            {
                'username': 'viewer',
                'password': 'viewer123',
                'role': 'user',
                'can_upload': False,
                'can_list_results': True,
                'force_change': True
            },
            {
                'username': 'fulluser',
                'password': 'fulluser123',
                'role': 'user',
                'can_upload': True,
                'can_list_results': True,
                'force_change': True
            },
            {
                'username': 'noperm',
                'password': 'noperm123',
                'role': 'user',
                'can_upload': False,
                'can_list_results': False,
                'force_change': True
            }
        ]

        for user_data in users_data:
            # Check if user exists
            existing = User.query.filter_by(username=user_data['username']).first()
            if existing:
                print(f"User {user_data['username']} already exists, skipping...")
                continue

            user = User(
                username=user_data['username'],
                role=user_data['role'],
                can_upload=user_data['can_upload'],
                can_list_results=user_data['can_list_results'],
                force_password_change=user_data['force_change']
            )
            user.set_password(user_data['password'])
            user.generate_token()
            db.session.add(user)
            db.session.commit()

            print(f"Created user: {user_data['username']}")
            print(f"  Token: {user.secret_token}")
            print(f"  Password: {user_data['password']}")
            print()

if __name__ == '__main__':
    create_users()
```

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review design document
- [ ] Backup existing `web_routes.py` and `sales_mcp_server.py`
- [ ] Create branch for authentication feature

### Phase 1: Environment Setup
- [ ] Install dependencies (Flask-Login, Flask-Bcrypt, Flask-WTF, Flask-SQLAlchemy)
- [ ] Create directory structure (templates, static, data)
- [ ] Verify installations

### Phase 2: Database Models
- [ ] Create `models.py` with User model
- [ ] Create `forms.py` with form classes
- [ ] Update `web_routes.py` with database initialization
- [ ] Test database creation

### Phase 3: Authentication System
- [ ] Add authentication decorators
- [ ] Create login/logout routes
- [ ] Create login template
- [ ] Test login flow

### Phase 4: Templates
- [ ] Create base template with navigation
- [ ] Create access denied template
- [ ] Create profile template
- [ ] Create custom CSS
- [ ] Test all templates

### Phase 5: Admin Interface
- [ ] Create admin routes
- [ ] Create admin templates
- [ ] Test admin user CRUD
- [ ] Verify permission system

### Phase 6: Profile & Password
- [ ] Create profile route
- [ ] Create password change functionality
- [ ] Test password change

### Phase 7: MCP Integration
- [ ] Update `sales_mcp_server.py` token verification
- [ ] Test MCP tools with database tokens
- [ ] Verify authorization flow

### Phase 8: Protect Existing Routes
- [ ] Add decorators to upload route
- [ ] Add decorators to list-results route
- [ ] Add decorators to download route
- [ ] Add root route redirect

### Phase 9: Error Handling
- [ ] Create CSRF error handler
- [ ] Test error scenarios
- [ ] Verify error messages

### Phase 10: Database Initialization
- [ ] Create database setup script
- [ ] Test database initialization
- [ ] Verify default users

### Phase 11: Testing & Verification
- [ ] Test all user roles
- [ ] Verify permissions
- [ ] Test admin functions
- [ ] Test MCP integration
- [ ] Test edge cases
- [ ] Create test users script

### Final Testing
- [ ] Login as admin, test all features
- [ ] Login as regular user, verify restrictions
- [ ] Test MCP tools with valid/invalid tokens
- [ ] Verify security measures (CSRF, sessions, etc.)
- [ ] Check all flash messages
- [ ] Verify responsive design
- [ ] Test logout/login flow
- [ ] Test password change on first login

---

## Security Verification Checklist

### Authentication Security
- [ ] Passwords are hashed with bcrypt (12 rounds)
- [ ] Sessions expire after 3 days
- [ ] "Remember me" extends to 30 days
- [ ] Tokens are unique and generated securely
- [ ] Cannot access admin routes without admin role
- [ ] Cannot access protected pages without login

### Session Security
- [ ] HttpOnly cookies enabled
- [ ] SameSite=Lax configured
- [ ] CSRF protection on all forms
- [ ] Session timeout enforced

### Authorization Security
- [ ] Permission checks on all protected routes
- [ ] Token validation in MCP server
- [ ] Cannot delete own admin account
- [ ] Cannot edit own permissions without admin override

### Input Validation
- [ ] Password minimum length enforced
- [ ] Username uniqueness enforced
- [ ] CSRF token validation
- [ ] File upload validation (.xlsx only, 50MB limit)

---

## Common Issues & Solutions

### Issue: Database Not Created
**Solution:** Ensure `data/` directory exists and application context is used when calling `create_db()`

### Issue: Import Errors
**Solution:** Ensure all imports are correct and dependencies are installed

### Issue: CSRF Token Missing
**Solution:** Verify `{{ form.hidden_tag() }}` is included in all forms

### Issue: Login Not Working
**Solution:** Check password hashing method matches bcrypt and verify user exists in database

### Issue: MCP Tools Not Recognizing Tokens
**Solution:** Verify `get_user_by_token()` function and ensure database connection is available

---

## Deployment Considerations

1. **Environment Variables:**
   - Set `SECRET_KEY` to a strong random value in production
   - Set `DATABASE_URL` for production database (PostgreSQL recommended)

2. **HTTPS:**
   - Set `SESSION_COOKIE_SECURE = True` in production
   - Use HTTPS for all traffic

3. **Database:**
   - Consider PostgreSQL or MySQL for production
   - Regular backups of user database
   - Connection pooling for scalability

4. **Logging:**
   - Enable application logging
   - Monitor failed login attempts
   - Log admin actions

5. **Password Policy:**
   - Enforce stronger password requirements
   - Consider password history
   - Implement account lockout after failed attempts

---

## Summary

This implementation plan provides a complete authentication system with:
- Username/password authentication with bcrypt hashing
- Role-based permissions (admin/user)
- Page-level access control
- Admin interface for user management
- MCP token-based authentication
- Secure session management
- CSRF protection
- Password change functionality

The implementation is structured in 11 phases, with clear file paths, code snippets, and verification steps. Each phase builds on the previous one, ensuring a solid foundation for the authentication system.
