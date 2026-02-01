# Authentication & Authorization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add username/password authentication with SQLite database, page-level permissions, and per-user tokens for MCP access

**Architecture:** Flask web server (port 8004) with Flask-Login sessions, Flask-Bcrypt password hashing, Flask-SQLAlchemy ORM, and updated MCP server (port 8003) token verification against database

**Tech Stack:** Flask-Login, Flask-Bcrypt, Flask-WTF, Flask-SQLAlchemy, SQLite, SQLAlchemy ORM

---

## Task 1: Environment Setup - Install Dependencies

**Files:**
- Modify: `requirements.txt` or `pyproject.toml`

**Step 1: Add dependencies to requirements.txt**

```bash
echo "Flask-Login>=0.6.0
Flask-Bcrypt>=1.0.0
Flask-WTF>=1.0.0
Flask-SQLAlchemy>=3.0.0
SQLAlchemy>=2.0.0
Werkzeug>=2.0.0" >> requirements.txt
```

**Step 2: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add Flask authentication stack dependencies"
```

---

## Task 2: Create Database Models

**Files:**
- Create: `models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
from models import User
from app import db

def test_user_model_creation():
    """Test User model can be created with attributes"""
    user = User(
        username="testuser",
        password_hash="hashedpassword",
        role="user",
        can_upload=False,
        can_list_results=True
    )
    assert user.username == "testuser"
    assert user.role == "user"
    assert user.can_upload == False
    assert user.can_list_results == True
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_models.py::test_user_model_creation -v
```
Expected: FAIL - ModuleNotFoundError: No module named 'models'

**Step 3: Write minimal implementation**

Create `models.py`:

```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    secret_token = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')
    can_upload = db.Column(db.Boolean, default=False)
    can_list_results = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def get_id(self):
        return str(self.id)

    def generate_token(self):
        """Generate a new secret token for the user"""
        self.secret_token = str(uuid.uuid4())
        return self.secret_token
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_models.py::test_user_model_creation -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py models.py
git commit -m "feat: add User model with authentication fields"
```

---

## Task 3: Create Flask Forms

**Files:**
- Create: `forms.py`

**Step 1: Write the failing test**

```python
# tests/test_forms.py
from forms import LoginForm, PasswordChangeForm, UserForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length

def test_login_form_structure():
    """Test LoginForm has required fields"""
    form = LoginForm()
    assert hasattr(form, 'username')
    assert hasattr(form, 'password')
    assert hasattr(form, 'remember_me')
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_forms.py::test_login_form_structure -v
```
Expected: FAIL - ModuleNotFoundError: No module named 'forms'

**Step 3: Write minimal implementation**

Create `forms.py`:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class PasswordChangeForm(FlaskForm):
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

class UserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    password = PasswordField('Password', validators=[Length(min=8, message='Password must be at least 8 characters')])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    can_upload = BooleanField('Can Upload Files')
    can_list_results = BooleanField('Can List Results', default=True)
    submit = SubmitField('Save User')

class TokenRegenerateForm(FlaskForm):
    submit = SubmitField('Regenerate Token')

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    can_upload = BooleanField('Can Upload Files')
    can_list_results = BooleanField('Can List Results')
    submit = SubmitField('Save User')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_forms.py::test_login_form_structure -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_forms.py forms.py
git commit -m "feat: add Flask forms for authentication and user management"
```

---

## Task 4: Initialize Database with Test Users

**Files:**
- Create: `init_db.py`
- Create: `create_test_users.py`

**Step 1: Write the failing test**

```python
# tests/test_db_init.py
from init_db import init_database
from pathlib import Path
import os

def test_database_initialization():
    """Test database is created"""
    db_path = Path("data/users.db")
    # Remove if exists
    if db_path.exists():
        os.remove(db_path)

    init_database()

    assert db_path.exists(), "Database file should be created"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_db_init.py::test_database_initialization -v
```
Expected: FAIL - ModuleNotFoundError: No module named 'init_db'

**Step 3: Write minimal implementation**

Create `init_db.py`:

```python
import os
from models import db, User
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize the database and create tables"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Set database URI
    os.environ.get('FLASK_APP', 'app.py')
    from app import app

    with app.app_context():
        # Create tables
        db.create_all()
        print("Database initialized successfully")

def create_test_users():
    """Create test users in the database"""
    from app import app
    from flask_bcrypt import generate_password_hash

    with app.app_context():
        # Create admin user
        admin = User(
            username='admin',
            role='admin',
            can_upload=True,
            can_list_results=True
        )
        admin.password_hash = generate_password_hash('admin123')
        admin.generate_token()

        # Create regular user (list only)
        user = User(
            username='user',
            role='user',
            can_upload=False,
            can_list_results=True
        )
        user.password_hash = generate_password_hash('user123')
        user.generate_token()

        # Create uploader user
        uploader = User(
            username='uploader',
            role='user',
            can_upload=True,
            can_list_results=True
        )
        uploader.password_hash = generate_password_hash('upload123')
        uploader.generate_token()

        db.session.add_all([admin, user, uploader])
        db.session.commit()

        print("Test users created:")
        print(f"  admin / admin123 (token: {admin.secret_token})")
        print(f"  user / user123 (token: {user.secret_token})")
        print(f"  uploader / upload123 (token: {uploader.secret_token})")

if __name__ == "__main__":
    init_database()
    create_test_users()
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_db_init.py::test_database_initialization -v
```
Expected: PASS

**Step 5: Run database initialization**

```bash
python init_db.py
```

**Step 6: Commit**

```bash
git add init_db.py create_test_users.py
git commit -m "feat: add database initialization scripts"
```

---

## Task 5: Update Flask App with Login Configuration

**Files:**
- Create: `app.py`

**Step 1: Write the failing test**

```python
# tests/test_app.py
from app import app, login_manager

def test_app_configuration():
    """Test app has login manager configured"""
    assert app is not None
    assert login_manager is not None
    assert app.config['SECRET_KEY'] is not None

def test_login_manager_callback():
    """Test user_loader callback is registered"""
    from flask_login import current_user
    assert hasattr(login_manager, 'user_loader')
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_app.py::test_app_configuration -v
```
Expected: FAIL - ModuleNotFoundError: No module named 'app'

**Step 3: Write minimal implementation**

Create `app.py`:

```python
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import timedelta
from models import db, User
from forms import LoginForm, PasswordChangeForm, UserForm, UserEditForm, PasswordResetForm, TokenRegenerateForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = db.func.now()
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=True)
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_app.py::test_app_configuration -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: add Flask app with login manager configuration"
```

---

## Task 6: Create Base Template with Navigation

**Files:**
- Create: `templates/base.html`

**Step 1: Write the failing test**

```python
# tests/test_templates.py
from app import app

def test_base_template_renders():
    """Test base template renders without errors"""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_fresh'] = True

        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_templates.py::test_base_template_renders -v
```
Expected: FAIL - FileNotFoundError: templates/base.html

**Step 3: Write minimal implementation**

Create `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sales Analysis Portal{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">Sales Analysis Portal</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    {% if current_user.is_authenticated %}
                        {% if current_user.can_upload %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('upload_file') }}">Upload Files</a>
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
                    {% endif %}
                </ul>
                <ul class="navbar-nav">
                    {% if current_user.is_authenticated %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('profile') }}">Profile</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                    </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <main class="container mt-4">
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

        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_templates.py::test_base_template_renders -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add templates/base.html tests/test_templates.py
git commit -m "feat: add base template with navigation"
```

---

## Task 7: Create Login Template

**Files:**
- Create: `templates/login.html`

**Step 1: Write minimal implementation**

Create `templates/login.html`:

```html
{% extends "base.html" %}

{% block title %}Login - {{ super() }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3 class="text-center">Login</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ form.hidden_tag() }}

                    <div class="mb-3">
                        {{ form.username.label(class="form-label") }}
                        {{ form.username(class="form-control", placeholder="Enter username") }}
                        {% if form.username.errors %}
                            {% for error in form.username.errors %}
                                <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        {% endif %}
                    </div>

                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control", placeholder="Enter password") }}
                        {% if form.password.errors %}
                            {% for error in form.password.errors %}
                                <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        {% endif %}
                    </div>

                    <div class="mb-3">
                        <div class="form-check">
                            {{ form.remember_me(class="form-check-input") }}
                            {{ form.remember_me.label(class="form-check-label") }}
                        </div>
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

**Step 2: Commit**

```bash
git add templates/login.html
git commit -m "feat: add login template"
```

---

## Task 8: Protect Upload and List Results Routes

**Files:**
- Modify: `web_routes.py`

**Step 1: Add authentication decorators**

Modify `web_routes.py`, add these decorators at the top:

```python
from flask_login import login_required, current_user
from functools import wraps

def require_upload_permission(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_upload:
            return render_template('access_denied.html',
                                 title='Access Denied',
                                 message='You do not have permission to upload files.')
        return f(*args, **kwargs)
    return decorated_function

def require_list_permission(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_list_results:
            return render_template('access_denied.html',
                                 title='Access Denied',
                                 message='You do not have permission to view results.')
        return f(*args, **kwargs)
    return decorated_function
```

**Step 2: Update upload route decorator**

Modify the existing `@app.route("/upload", methods=["GET", "POST"])`:

Change from:
```python
def upload_file():
```

To:
```python
@require_upload_permission
def upload_file():
```

**Step 3: Update list results route decorator**

Modify the existing `@app.route("/list-results", methods=["GET", "POST"])`:

Change from:
```python
def list_results():
```

To:
```python
@require_list_permission
def list_results():
```

**Step 4: Test with browser**

```bash
python -c "from app import app; app.run(debug=True, port=8004)"
```
Visit: http://localhost:8004/login
Expected: Can login, redirect works based on permissions

**Step 5: Commit**

```bash
git add web_routes.py
git commit -m "feat: protect upload and list routes with authentication"
```

---

## Task 9: Create Access Denied Template

**Files:**
- Create: `templates/access_denied.html`

**Step 1: Write minimal implementation**

Create `templates/access_denied.html`:

```html
{% extends "base.html" %}

{% block title %}{{ title }} - {{ super() }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="alert alert-warning" role="alert">
            <h4 class="alert-heading">{{ title }}</h4>
            <p>{{ message }}</p>
            <hr>
            <p class="mb-0">
                <a href="{{ url_for('index') }}" class="btn btn-primary">Go Home</a>
                <a href="{{ url_for('profile') }}" class="btn btn-secondary">View Profile</a>
            </p>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 2: Commit**

```bash
git add templates/access_denied.html
git commit -m "feat: add access denied template"
```

---

## Task 10: Create Profile Page with Token Display

**Files:**
- Modify: `app.py`

**Step 1: Add profile route to app.py**

Add to `app.py`:

```python
from forms import PasswordChangeForm, TokenRegenerateForm
from flask_bcrypt import check_password_hash, generate_password_hash

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with token display and password change"""
    password_form = PasswordChangeForm()
    token_form = TokenRegenerateForm()

    if password_form.validate_on_submit():
        # Verify current password
        if check_password_hash(current_user.password_hash, password_form.current_password.data):
            current_user.password_hash = generate_password_hash(password_form.new_password.data)
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
```

**Step 2: Create profile template**

Create `templates/profile.html`:

```html
{% extends "base.html" %}

{% block title %}Profile - {{ super() }}{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                <h4>User Information</h4>
            </div>
            <div class="card-body">
                <p><strong>Username:</strong> {{ current_user.username }}</p>
                <p><strong>Role:</strong> {{ current_user.role|title }}</p>
                <p><strong>Permissions:</strong></p>
                <ul>
                    <li>Upload Files: {{ 'Yes' if current_user.can_upload else 'No' }}</li>
                    <li>List Results: {{ 'Yes' if current_user.can_list_results else 'No' }}</li>
                </ul>
                <p><strong>Last Login:</strong> {{ current_user.last_login or 'Never' }}</p>
            </div>
        </div>
    </div>

    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                <h4>MCP Access Token</h4>
            </div>
            <div class="card-body">
                <p>Use this token with MCP tools for programmatic access:</p>
                <div class="input-group mb-3">
                    <input type="text" class="form-control" value="{{ current_user.secret_token }}" readonly id="tokenDisplay">
                    <button class="btn btn-outline-secondary" type="button" onclick="copyToken()">Copy</button>
                </div>
                <div class="form-text">
                    Pass this token via Authorization header: <code>Bearer {{ current_user.secret_token }}</code>
                </div>

                <hr>
                <form method="POST">
                    {{ token_form.hidden_tag() }}
                    {{ token_form.submit(class="btn btn-warning btn-sm",
                                       onclick="return confirm('Are you sure you want to regenerate your token?')") }}
                </form>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>Change Password</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ password_form.hidden_tag() }}

                    <div class="mb-3">
                        {{ password_form.current_password.label(class="form-label") }}
                        {{ password_form.current_password(class="form-control") }}
                        {% for error in password_form.current_password.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        {{ password_form.new_password.label(class="form-label") }}
                        {{ password_form.new_password(class="form-control") }}
                        {% for error in password_form.new_password.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        {{ password_form.confirm_password.label(class="form-label") }}
                        {{ password_form.confirm_password(class="form-control") }}
                        {% for error in password_form.confirm_password.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>

                    {{ password_form.submit(class="btn btn-primary") }}
                </form>
            </div>
        </div>
    </div>
</div>

<script>
function copyToken() {
    const tokenDisplay = document.getElementById('tokenDisplay');
    tokenDisplay.select();
    document.execCommand('copy');

    // Show feedback
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => {
        btn.textContent = originalText;
    }, 2000);
}
</script>
{% endblock %}
```

**Step 3: Commit**

```bash
git add app.py templates/profile.html
git commit -m "feat: add profile page with token display and password change"
```

---

## Task 11: Create Admin User Management Interface

**Files:**
- Create: `templates/admin_users.html`
- Modify: `app.py`

**Step 1: Add admin routes to app.py**

Add to `app.py`:

```python
from flask import abort
from forms import UserForm, UserEditForm, PasswordResetForm

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

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
        import uuid
        token = str(uuid.uuid4())

        user = User(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data),
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
        user.password_hash = generate_password_hash(form.password.data)
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
```

**Step 2: Create admin users template**

Create `templates/admin_users.html`:

```html
{% extends "base.html" %}

{% block title %}User Management - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>User Management</h2>
    <a href="{{ url_for('admin_add_user') }}" class="btn btn-primary">Add User</a>
</div>

<div class="card">
    <div class="card-body">
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
                    <td>{{ user.role|title }}</td>
                    <td>
                        <span class="badge bg-{{ 'success' if user.can_upload else 'secondary' }}">
                            {{ 'Yes' if user.can_upload else 'No' }}
                        </span>
                    </td>
                    <td>
                        <span class="badge bg-{{ 'success' if user.can_list_results else 'secondary' }}">
                            {{ 'Yes' if user.can_list_results else 'No' }}
                        </span>
                    </td>
                    <td>{{ user.created_at.strftime('%Y-%m-%d') }}</td>
                    <td>{{ user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never' }}</td>
                    <td>
                        <a href="{{ url_for('admin_edit_user', user_id=user.id) }}" class="btn btn-sm btn-info">Edit</a>
                        <a href="{{ url_for('admin_reset_password', user_id=user.id) }}" class="btn btn-sm btn-warning">Reset Password</a>
                        <form method="POST" action="{{ url_for('admin_regenerate_token', user_id=user.id) }}" style="display: inline;">
                            <button type="submit" class="btn btn-sm btn-secondary">Regenerate Token</button>
                        </form>
                        {% if user.id != current_user.id %}
                        <a href="{{ url_for('admin_delete_user', user_id=user.id) }}" class="btn btn-sm btn-danger">Delete</a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

**Step 3: Create admin user form template**

Create `templates/admin_user_form.html`:

```html
{% extends "base.html" %}

{% block title %}{{ title }} - {{ super() }}{% endblock %}

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
                        {{ form.username(class="form-control") }}
                        {% for error in form.username.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>

                    {% if not user or 'password' in form %}
                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control") }}
                        {% for error in form.password.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                        {% if not user %}
                        <div class="form-text">User will be required to change this password on first login</div>
                        {% endif %}
                    </div>
                    {% endif %}

                    <div class="mb-3">
                        {{ form.role.label(class="form-label") }}
                        {{ form.role(class="form-select") }}
                        {% for error in form.role.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>

                    <div class="mb-3">
                        <div class="form-check">
                            {{ form.can_upload(class="form-check-input") }}
                            {{ form.can_upload.label(class="form-check-label") }}
                        </div>
                    </div>

                    <div class="mb-3">
                        <div class="form-check">
                            {{ form.can_list_results(class="form-check-input") }}
                            {{ form.can_list_results.label(class="form-check-label") }}
                        </div>
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

**Step 4: Create admin delete user template**

Create `templates/admin_delete_user.html`:

```html
{% extends "base.html" %}

{% block title %}{{ title }} - {{ super() }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-danger text-white">
                <h3>{{ title }}</h3>
            </div>
            <div class="card-body">
                <p>Are you sure you want to delete the user <strong>{{ user.username }}</strong>?</p>
                <p class="text-danger">This action cannot be undone!</p>

                <form method="POST">
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-danger">Delete User</button>
                        <a href="{{ url_for('admin_users') }}" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 5: Create admin reset password template**

Create `templates/admin_reset_password.html`:

```html
{% extends "base.html" %}

{% block title %}{{ title }} - {{ super() }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3>{{ title }} - {{ user.username }}</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ form.hidden_tag() }}

                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control", placeholder="Enter new password") }}
                        {% for error in form.password.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                        <div class="form-text">User will be required to change this password on next login</div>
                    </div>

                    <div class="mb-3">
                        {{ form.confirm_password.label(class="form-label") }}
                        {{ form.confirm_password(class="form-control", placeholder="Confirm password") }}
                        {% for error in form.confirm_password.errors %}
                            <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>

                    <div class="d-grid gap-2">
                        {{ form.submit(class="btn btn-warning") }}
                        <a href="{{ url_for('admin_users') }}" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 6: Commit**

```bash
git add app.py templates/admin_*.html
git commit -m "feat: add admin user management interface"
```

---

## Task 12: Update MCP Server Token Verification

**Files:**
- Modify: `sales_mcp_server.py`

**Step 1: Write the failing test**

```python
# tests/test_mcp_auth.py
from sales_mcp_server import verify_authorization
from unittest.mock import patch, MagicMock

def test_verify_valid_token():
    """Test token verification with valid token"""
    with patch('sales_mcp_server.get_user_by_token') as mock_get_user:
        mock_user = MagicMock()
        mock_user.username = 'testuser'
        mock_get_user.return_value = mock_user

        result = verify_authorization()
        assert 'valid token' in result
        assert 'testuser' in result

def test_verify_invalid_token():
    """Test token verification with invalid token"""
    with patch('sales_mcp_server.get_user_by_token') as mock_get_user:
        mock_get_user.return_value = None

        result = verify_authorization()
        assert 'invalid token' in result
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_mcp_auth.py::test_verify_valid_token -v
```
Expected: FAIL - AttributeError: 'function' object has no attribute 'return_value'

**Step 3: Modify sales_mcp_server.py**

First, add import at top:

```python
from models import User
```

Then, modify the `verify_authorization()` function:

```python
def verify_authorization() -> str:
    """Verify the Authorization header and return the token or error message."""
    from fastmcp.server.dependencies import get_http_headers
    headers = get_http_headers()
    auth = headers.get("authorization") or headers.get("Authorization")

    if not auth:
        print("no api key is found")
        return "no api key is found"

    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
    else:
        token = auth.strip()

    print(f"token: {token}")

    # Check token against database
    user = User.query.filter_by(secret_token=token).first()

    if user:
        return f"valid token for user: {user.username}"
    else:
        return f"invalid token: {token}"
```

**Step 4: Remove global API_TOKEN**

Remove from line 491-512 in `sales_mcp_server.py`:
- Remove: `API_TOKEN = "1234567890"`
- Remove: The old verification logic

**Step 5: Add database context**

Modify the `if __name__ == "__main__":` section:

```python
if __name__ == "__main__":
    # Start both MCP server and web interface
    import threading
    from app import app

    # Start Flask web server in a separate thread
    def run_web_server():
        import web_routes
        web_routes.app.run(host="0.0.0.0", port=8004, debug=False, use_reloader=False)

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Start MCP server with database context
    with app.app_context():
        print("Starting MCP server on port 8003...")
        print("Starting web interface on port 8004...")
        app.run(transport="http", host="0.0.0.0", port=8003)
```

**Step 6: Run test to verify it passes**

```bash
python -m pytest tests/test_mcp_auth.py -v
```
Expected: PASS

**Step 7: Commit**

```bash
git add sales_mcp_server.py tests/test_mcp_auth.py
git commit -m "feat: update MCP server token verification to use database"
```

---

## Task 13: Integration Testing

**Step 1: Test database initialization**

```bash
python init_db.py
```
Expected: "Database initialized successfully" and "Test users created" with 3 users

**Step 2: Start application**

```bash
python app.py
```

**Step 3: Test login flow**

1. Visit http://localhost:8004/login
2. Login with `admin` / `admin123`
3. Expected: Redirect to upload page
4. Check navigation shows: Upload Files, List Results, Admin, Profile

**Step 4: Test permissions**

1. Logout
2. Login with `user` / `user123`
3. Expected: Redirect to list results page
4. Check navigation shows only: List Results, Profile
5. Try to visit /upload directly
6. Expected: Access denied page

**Step 5: Test admin interface**

1. Login as admin
2. Visit /admin/users
3. Expected: See all 3 users
4. Click "Edit" on user account
5. Toggle permissions and save
6. Expected: Changes saved message

**Step 6: Test MCP token**

1. Login as admin
2. Visit /profile
3. Copy token
4. Use token with MCP tools:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8003/upload-input
   ```
5. Expected: "valid token for user: admin"

**Step 7: Commit**

```bash
git add .
git commit -m "feat: complete authentication and authorization system"
```

---

## Task 14: Create .gitignore for Sensitive Files

**Files:**
- Modify: `.gitignore`

**Step 1: Add entries**

Add to `.gitignore`:

```gitignore
# Authentication and database
data/
*.db

# Secrets
.env
.env.local

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore for sensitive data and cache files"
```

---

**Plan complete and saved to `docs/plans/2026-02-01-authentication-implementation.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
