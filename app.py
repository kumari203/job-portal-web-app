import os
from datetime import datetime
from flask import (Flask, render_template, redirect, url_for, flash,request, send_from_directory, session)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (LoginManager, UserMixin, login_user, logout_user,login_required, current_user)
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField,TextAreaField, SubmitField, FileField,RadioField,IntegerField)
from wtforms.validators import InputRequired, Email, Length, DataRequired, EqualTo,NumberRange
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from functools import wraps
from flask_migrate import Migrate
from dotenv import load_dotenv

# -------------------------
# CONFIG
# -------------------------
load_dotenv()
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobportal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Mail (example Gmail configuration - use App Password or SMTP provider)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = MAIL_USERNAME  # change
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD    # change (App Password if Gmail)
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


# DB + Auth
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


# -------------------------
# MODELS
# -------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)   # fullname used everywhere
    email = db.Column(db.String(120), unique=True, nullable=False)
    password= db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="jobseeker")

    jobs = db.relationship("Job", backref="employer", lazy=True)
    applications = db.relationship("Application", backref="applicant", lazy=True)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    salary = db.Column(db.Float, nullable=False) 
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(100), nullable=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    applications = db.relationship('Application',backref='job',cascade='all, delete-orphan')



class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

def role_required(required_role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role != required_role:
                flash("Access denied!", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
# -------------------------
# LOGIN MANAGER
# -------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



# -------------------------
# FORMS
# -------------------------
class RegisterForm(FlaskForm):
    fullname = StringField("Full Name", validators=[InputRequired(), Length(min=3)])
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password",validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    role = RadioField("Role", choices=[('jobseeker','Job Seeker'),
                                       ('employer','Employer'),
                                       ('admin','Admin')], validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ResetRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField( "Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Reset Password")


class JobForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    company = StringField("Company", validators=[InputRequired()])
    salary = IntegerField("Salary (in INR)", validators=[InputRequired(),NumberRange(min=0, message="Salary must be a positive number")])
    location = StringField("Location", validators=[InputRequired()])
    description = TextAreaField("Description", validators=[InputRequired()])
    submit = SubmitField("Save Job")


class ApplyForm(FlaskForm):
    cover_letter = TextAreaField("Cover Letter")
    resume = FileField("Upload Resume")
    submit = SubmitField("Apply")


# -------------------------
# HELPERS
# -------------------------


def send_reset_email(user):
    """Generate token and send reset email (uses Flask-Mail)."""
    token = s.dumps(user.email, salt="password-reset")
    link = url_for("reset_token", token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = (
        f"Hi {user.fullname},\n\n"
        f"Click the link to reset your password:\n{link}\n\n"
        "If you didn't request this, you can ignore this email.\n"
        "This link expires in 10 minutes."
    )
    mail.send(msg)


# -------------------------
# ROUTES
# -------------------------
# Portal route
@app.route("/")
def index():
    # Force login to view portal — redirect to login if not authenticated
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    page = request.args.get("page", 1, type=int)
    jobs = Job.query.order_by(Job.posted_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template("index.html", jobs=jobs)


# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)

        new_user = User(
            fullname=form.fullname.data,
            email=form.email.data,
            password=hashed,
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)




# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Correct password checking
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful!", "success")

            # Redirect by role
            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            elif user.role == "employer":
                return redirect(url_for('employer_dashboard'))
            else:
                return redirect(url_for('jobseeker_dashboard'))

        else:
            flash("Invalid login details", "danger")

    return render_template('login.html', form=form)





# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


# Forgot password
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = ResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                send_reset_email(user)
            except Exception as e:
                # don't expose raw error to user; log server-side if you want
                print("Mail send error:", e)
                flash("Unable to send email. Contact admin or try later.", "danger")
                return redirect(url_for("forgot_password"))

        # Always show the same message to avoid leaking which emails are registered
        flash("If this email exists, a password reset link has been sent.", "info")
        return redirect(url_for("login"))

    return render_template("forgot_password.html", form=form)


# Token verify and reset
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    try:
        email = s.loads(token, salt="password-reset", max_age=600)  # 10 minutes
    except SignatureExpired:
        flash("This reset link has expired.", "danger")
        return redirect(url_for("forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "danger")
        return redirect(url_for("forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid reset request.", "danger")
        return redirect(url_for("forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Password reset successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", form=form)

# Admin dashboard
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    users = User.query.all()
    jobs = Job.query.all()
    return render_template("admin_dashboard.html", users=users, jobs=jobs)


# Employer dashboard
@app.route('/employer/dashboard')
@login_required
@role_required('employer')
def employer_dashboard():
    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    return render_template("employer_dashboard.html", jobs=jobs)


# Jobseeker dashboard
@app.route("/jobseeker/dashboard")
@login_required
def jobseeker_dashboard():
    search = request.args.get("q", "")
    location = request.args.get("location", "")
    category = request.args.get("category", "")
    company = request.args.get("company", "")

    jobs = Job.query

    # Keyword search (title + description)
    if search:
        jobs = jobs.filter(
            Job.title.ilike(f"%{search}%") |
            Job.description.ilike(f"%{search}%")
        )

    # Location filter
    if location:
        jobs = jobs.filter(Job.location.ilike(f"%{location}%"))

    # Category filter
    if category:
        jobs = jobs.filter(Job.category.ilike(f"%{category}%"))

    # Company filter
    if company:
        jobs = jobs.filter(Job.company.ilike(f"%{company}%"))

    jobs = jobs.all()

    return render_template(
        "jobseeker_dashboard.html",
        jobs=jobs,
        search_query=search,
        selected_location=location,
        selected_category=category,
        selected_company=company
    )






# Post job
@app.route("/post-job", methods=["GET", "POST"])
@login_required
def post_job():
    if current_user.role != "employer":
        flash("Only employers can post jobs!", "danger")
        return redirect(url_for("login"))

    form = JobForm()

    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            company=form.company.data,
            salary=form.salary.data,
            location=form.location.data,
            description=form.description.data,
            employer_id=current_user.id
        )

        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully!", "success")
        return redirect(url_for("employer_dashboard"))

    return render_template("post_job.html", form=form)

# Edit job
@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        flash("You are not allowed to edit this job!", "danger")
        return redirect(url_for("employer_dashboard"))

    form = JobForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data
        job.company = form.company.data
        job.salary = form.salary.data
        job.location = form.location.data
        job.description = form.description.data

        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for("employer_dashboard"))

    return render_template("edit_job.html", form=form)


# Delete job(Employer's)
@app.route("/delete-job/<int:job_id>")
@login_required
def employer_delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        flash("You cannot delete this job!", "danger")
        return redirect(url_for("employer_dashboard"))

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully!", "success")
    return redirect(url_for("employer_dashboard"))


# Job detail + apply
@app.route("/apply/<int:job_id>")
@login_required
@role_required('jobseeker')
def apply(job_id):
    job = Job.query.get_or_404(job_id)

    # Prevent duplicate applications
    existing = Application.query.filter_by(job_id=job.id, user_id=current_user.id).first()
    if existing:
        flash("You have already applied for this job!", "warning")
        return redirect(url_for('jobseeker_dashboard'))

    application = Application(job_id=job.id, user_id=current_user.id)
    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully!", "success")
    return redirect(url_for('jobseeker_dashboard'))

# In admin dashboard delete user route
@app.route('/admin/delete_user/<int:user_id>')
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash("You cannot delete your own admin account!", "danger")
        return redirect(url_for('admin_dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))

# In admin dashboard change role route
@app.route('/admin/change_role/<int:user_id>/<new_role>')
@login_required
@role_required('admin')
def change_role(user_id, new_role):
    user = User.query.get_or_404(user_id)

    valid_roles = ['admin', 'employer', 'jobseeker']
    if new_role not in valid_roles:
        flash("Invalid role!", "danger")
        return redirect(url_for('admin_dashboard'))

    user.role = new_role
    db.session.commit()
    flash("User role updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# Delete Job(admin's)
@app.route('/admin/delete_job/<int:job_id>')
@login_required
@role_required('admin')
def admin_delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    db.session.delete(job)
    db.session.commit()
    flash("Job deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))



# After-request headers (no login_required here)
@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
