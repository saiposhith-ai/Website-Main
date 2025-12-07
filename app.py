import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from PIL import Image
import secrets
import json
import re
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-permanent-secret-key-here-make-it-very-long-and-random-aB3dE5fG7hI9jK2lM4nO6pQ8rS1tU3vW5xY7zA9bC1dE3fG5hI7jK9lM2nO4pQ6rS8tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO2pQ4rS6tU8vW1'

app.config['PERMANENT_SESSION_LIFETIME'] = 86400  
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://")


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Use /tmp for uploads on Vercel
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'employees'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'banners'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'partners'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'heroes'), exist_ok=True)

db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='SHARMIC')
    logo_path = db.Column(db.String(200), default='')
    favicon_path = db.Column(db.String(200), default='')
    meta_title = db.Column(db.String(200), default='SHARMIC - Payment Solutions')
    meta_description = db.Column(db.Text, default='We engineer payments for global scale')
    meta_keywords = db.Column(db.Text, default='payments, fintech, payment gateway')
    footer_text = db.Column(db.Text, default='Copyright 2025. SHARMIC Technologies. All rights reserved.')
    contact_email = db.Column(db.String(120), default='contact@sharmic.com')
    contact_phone = db.Column(db.String(50), default='+91-1234567890')
    address = db.Column(db.Text, default='')
    social_linkedin = db.Column(db.String(200), default='')
    social_twitter = db.Column(db.String(200), default='')
    social_facebook = db.Column(db.String(200), default='')
    social_instagram = db.Column(db.String(200), default='https://www.instagram.com/shramic.info')

class HeroSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(50), nullable=False, unique=True)
    
    badge_text = db.Column(db.String(100), default='WELCOME')
    badge_icon_type = db.Column(db.String(20), default='none')  
    badge_icon_content = db.Column(db.Text, default='')  
    
    title_line1 = db.Column(db.String(200), default='Main Title')
    title_line2 = db.Column(db.String(200), default='Highlighted Text')
    title_style = db.Column(db.String(20), default='gradient') 
    
    subtitle = db.Column(db.Text, default='Description text goes here.')
    
    cta_text = db.Column(db.String(100), default='Get Started')
    cta_link = db.Column(db.String(200), default='/contact')
    cta_style = db.Column(db.String(20), default='solid')
    
    background_type = db.Column(db.String(20), default='particles') 
    background_image_path = db.Column(db.String(200), default='')
    background_video_url = db.Column(db.String(300), default='')
    background_overlay_opacity = db.Column(db.Integer, default=80)  
    
    text_alignment = db.Column(db.String(20), default='center')  
    min_height = db.Column(db.String(20), default='100vh') 
    
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<HeroSection {self.page}>'

class StatCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(50), nullable=False)  # 'home' or 'about'
    number = db.Column(db.String(50), nullable=False)
    label_line1 = db.Column(db.String(100), nullable=False)
    label_line2 = db.Column(db.String(100), default='')
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(50), default='⚡')
    icon_path = db.Column(db.String(200), default='') 
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, default=5)
    text = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_title = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), default='') 
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class GlobalHub(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    flag = db.Column(db.String(10), nullable=False) 
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    maps_link = db.Column(db.String(500), default='#')
    is_featured = db.Column(db.Boolean, default=False)
    is_coming_soon = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class Investor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_path = db.Column(db.String(200), default='')
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class FormulaItem(db.Model):
    __tablename__ = 'formula_items'
    
    id = db.Column(db.Integer, primary_key=True)
    step_number = db.Column(db.Integer, nullable=False)  # The numbered step (1, 2, 3, etc.)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FormulaItem {self.step_number}: {self.title}>'

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), default='other') 
    gender = db.Column(db.String(10), default='male')
    image_path = db.Column(db.String(200), default='')
    bio = db.Column(db.Text, default='')
    email = db.Column(db.String(120), default='') 
    linkedin = db.Column(db.String(200), default='')  
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    meta_title = db.Column(db.String(200), default='')
    meta_description = db.Column(db.Text, default='')
    content = db.Column(db.Text, default='')
    template = db.Column(db.String(50), default='page.html')
    active = db.Column(db.Boolean, default=True)
    show_in_nav = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_path = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(200), default='')
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(50), default='Full-time')  # Full-time, Part-time, Contract, Internship
    experience_level = db.Column(db.String(50), default='Mid-level')  # Entry, Mid-level, Senior, Lead
    salary_range = db.Column(db.String(100), default='')
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, default='')
    responsibilities = db.Column(db.Text, default='')
    benefits = db.Column(db.Text, default='')
    skills = db.Column(db.Text, default='')  # Comma-separated
    external_link = db.Column(db.String(300), default='https://shramicintern.pythonanywhere.com/')
    featured = db.Column(db.Boolean, default=False)
    remote_allowed = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), default='')
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    issue = db.Column(db.String(200), default='')
    message = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class FooterLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    linkedin = db.Column(db.String(200), default='')
    portfolio = db.Column(db.String(200), default='')
    resume_path = db.Column(db.String(200), default='')
    cover_letter = db.Column(db.Text, default='')
    years_experience = db.Column(db.String(20), default='')
    status = db.Column(db.String(20), default='new')  # new, reviewing, shortlisted, rejected, hired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    career = db.relationship('Career', backref='applications')
        
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def initialize_default_footer_links():
    """Initialize default footer links if none exist"""
    
    if FooterLink.query.count() == 0:
        default_links = [
            # Company Links
            {'category': 'Company', 'title': 'About Us', 'url': '/about', 'order': 1},
            {'category': 'Company', 'title': 'Our Team', 'url': '/team', 'order': 2},
            {'category': 'Company', 'title': 'Careers', 'url': '/careers', 'order': 3},
            {'category': 'Company', 'title': 'Contact', 'url': '/contact', 'order': 4},
            
            # Legal Links
            {'category': 'Legal', 'title': 'Privacy Policy', 'url': '/privacy-policy', 'order': 1},
            {'category': 'Legal', 'title': 'Terms & Conditions', 'url': '/terms-conditions', 'order': 2},
            {'category': 'Legal', 'title': 'Cookie Policy', 'url': '/cookie-policy', 'order': 3},
            {'category': 'Legal', 'title': 'Data Protection', 'url': '/data-protection', 'order': 4},
            
            # Support Links
            {'category': 'Support', 'title': 'Contact Support', 'url': '/contact', 'order': 1},
            {'category': 'Support', 'title': 'Documentation', 'url': '/docs', 'order': 2},
            {'category': 'Support', 'title': 'FAQs', 'url': '/faq', 'order': 3},
            {'category': 'Support', 'title': 'Status', 'url': '/status', 'order': 4},
        ]
        
        for link_data in default_links:
            link = FooterLink(
                category=link_data['category'],
                title=link_data['title'],
                url=link_data['url'],
                order=link_data['order'],
                active=True
            )
            db.session.add(link)
        
        db.session.commit()
        print("Default footer links initialized successfully!")

def save_image(file, folder='uploads'):
    """
    Returns: path relative to /static, e.g. 'uploads/logos/file.png'
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"

        # e.g. local: static/uploads/logos
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)

        if filename.lower().endswith('.svg'):
            file.save(filepath)
        else:
            img = Image.open(file)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(filepath, quality=85, optimize=True)

        # 🔴 IMPORTANT: include 'uploads/' here
        return f'uploads/{folder}/{filename}'
    return None


def get_site_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

def get_navigation_pages():
    return Page.query.filter_by(active=True, show_in_nav=True).order_by(Page.order).all()

def detect_department(designation):
    """Auto-detect department based on designation keywords"""
    designation_lower = designation.lower()
    
    if any(keyword in designation_lower for keyword in ['ceo', 'cto', 'cfo', 'director', 'head', 'vp', 'president', 'founder', 'chief']):
        return 'leadership'
    elif any(keyword in designation_lower for keyword in ['engineer', 'developer', 'programmer', 'architect', 'devops']):
        return 'engineering'
    elif any(keyword in designation_lower for keyword in ['design', 'ui', 'ux', 'creative', 'graphic']):
        return 'design'
    elif any(keyword in designation_lower for keyword in ['manager', 'operations', 'analyst', 'coordinator', 'admin', 'hr', 'marketing', 'sales']):
        return 'operations'
    else:
        return 'other'
    
@app.context_processor
def inject_globals():
    try:
        unread_contacts = ContactSubmission.query.filter_by(read=False).count()
    except:
        unread_contacts = 0
    
    return {
        'site_settings': get_site_settings(),
        'nav_pages': get_navigation_pages(),
        'current_year': datetime.now().year,
        'unread_contacts': unread_contacts
    }

@app.context_processor
def inject_footer_links():
    """Make footer links available to all templates"""
    footer_links = FooterLink.query.filter_by(active=True).order_by(FooterLink.category, FooterLink.order).all()
    
    # Group links by category
    grouped_links = {}
    for link in footer_links:
        if link.category not in grouped_links:
            grouped_links[link.category] = []
        grouped_links[link.category].append(link)
    
    return {'footer_links_grouped': grouped_links}

@app.route('/')
def index():
    hero = HeroSection.query.filter_by(page='home', active=True).first()
    stats = StatCard.query.filter_by(page='home', active=True).order_by(StatCard.order).all()
    features = Feature.query.filter_by(active=True).order_by(Feature.order).all()
    partners = Partner.query.filter_by(active=True).order_by(Partner.order).all()
    testimonials = Testimonial.query.filter_by(active=True).order_by(Testimonial.order).all()
    
    return render_template('index.html', 
                         hero=hero, 
                         stats=stats, 
                         features=features,
                         partners=partners,
                         testimonials=testimonials)

@app.route('/about')
def about():
    hero = HeroSection.query.filter_by(page='about', active=True).first()
    stats = StatCard.query.filter_by(page='about', active=True).order_by(StatCard.order).all()  
    partners = Partner.query.filter_by(active=True).order_by(Partner.order).all()
    hubs = GlobalHub.query.filter_by(active=True).order_by(GlobalHub.order).all()
    investors = Investor.query.filter_by(active=True).order_by(Investor.order).all()
    formula_items = FormulaItem.query.filter_by(active=True).order_by(FormulaItem.step_number).all()
    
    return render_template('about.html',
                         hero=hero,
                         stats=stats,
                         partners=partners,
                         hubs=hubs,
                         investors=investors,
                         formula_items=formula_items)

@app.route('/team')
def team():
    hero = HeroSection.query.filter_by(page='team', active=True).first()
    employees = Employee.query.filter_by(active=True).order_by(Employee.order).all()
    
    # Calculate stats
    leadership_pattern = re.compile(r'CEO|CTO|CFO|Director|Head|VP|President|Founder|CIO', re.IGNORECASE)
    senior_pattern = re.compile(r'Manager|Lead|Senior', re.IGNORECASE)
    tech_pattern = re.compile(r'Engineer|Developer|Designer|Analyst', re.IGNORECASE)
    
    leadership_count = sum(1 for emp in employees if leadership_pattern.search(emp.designation))
    senior_count = sum(1 for emp in employees if senior_pattern.search(emp.designation))
    tech_count = sum(1 for emp in employees if tech_pattern.search(emp.designation))
    
    return render_template('team.html', 
                         hero=hero,
                         employees=employees,
                         leadership_count=leadership_count,
                         senior_count=senior_count,
                         tech_count=tech_count)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        submission = ContactSubmission(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name', ''),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            issue=request.form.get('issue', ''),
            message=request.form.get('message', '')
        )
        db.session.add(submission)
        db.session.commit()
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    partners = Partner.query.filter_by(active=True).order_by(Partner.order).all()
    return render_template('contact.html', partners=partners)

@app.route('/careers')
def careers():
    # Get filter parameters
    department = request.args.get('department', '')
    job_type = request.args.get('job_type', '')
    location = request.args.get('location', '')
    
    # Base query
    query = Career.query.filter_by(active=True)
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    if job_type:
        query = query.filter_by(job_type=job_type)
    if location:
        query = query.filter(Career.location.ilike(f'%{location}%'))
    
    jobs = query.order_by(Career.created_at.desc()).all()
    
    # Get unique values for filters
    departments = db.session.query(Career.department).filter_by(active=True).distinct().all()
    job_types = db.session.query(Career.job_type).filter_by(active=True).distinct().all()
    locations = db.session.query(Career.location).filter_by(active=True).distinct().all()
    
    return render_template('careers.html', 
                         jobs=jobs,
                         departments=[d[0] for d in departments],
                         job_types=[j[0] for j in job_types],
                         locations=[l[0] for l in locations],
                         current_filters={
                             'department': department,
                             'job_type': job_type,
                             'location': location
                         })

@app.route('/privacy-policy')
def privacy_policy():
    """Render Privacy Policy page"""
    page = Page.query.filter_by(slug='privacy-policy', active=True).first()
    if not page:
        # Create default page if it doesn't exist
        page = Page(
            slug='privacy-policy',
            title='Privacy Policy',
            meta_title='Privacy Policy - ' + get_site_settings().site_name,
            meta_description='Our privacy policy explains how we collect, use, and protect your personal information.',
            content='<h2>Privacy Policy Content</h2><p>Please update this content from the admin panel.</p>',
            template='legal.html',
            active=True,
            show_in_nav=False
        )
        db.session.add(page)
        db.session.commit()
    
    return render_template('legal.html', page=page)

@app.route('/terms-conditions')
def terms_conditions():
    """Render Terms & Conditions page"""
    page = Page.query.filter_by(slug='terms-conditions', active=True).first()
    if not page:
        # Create default page if it doesn't exist
        page = Page(
            slug='terms-conditions',
            title='Terms & Conditions',
            meta_title='Terms & Conditions - ' + get_site_settings().site_name,
            meta_description='Terms and conditions for using our services.',
            content='<h2>Terms & Conditions Content</h2><p>Please update this content from the admin panel.</p>',
            template='legal.html',
            active=True,
            show_in_nav=False
        )
        db.session.add(page)
        db.session.commit()
    
    return render_template('legal.html', page=page)

# Additional legal page routes
@app.route('/cookie-policy')
def cookie_policy():
    """Render Cookie Policy page"""
    page = Page.query.filter_by(slug='cookie-policy', active=True).first()
    if not page:
        page = Page(
            slug='cookie-policy',
            title='Cookie Policy',
            meta_title='Cookie Policy - ' + get_site_settings().site_name,
            meta_description='Learn about how we use cookies on our website.',
            content='<h2>Cookie Policy</h2><p>Please update this content from the admin panel.</p>',
            template='legal.html',
            active=True,
            show_in_nav=False
        )
        db.session.add(page)
        db.session.commit()
    
    return render_template('legal.html', page=page)

@app.route('/refund-policy')
def refund_policy():
    """Render Refund Policy page"""
    page = Page.query.filter_by(slug='refund-policy', active=True).first()
    if not page:
        page = Page(
            slug='refund-policy',
            title='Refund Policy',
            meta_title='Refund Policy - ' + get_site_settings().site_name,
            meta_description='Our refund and cancellation policy.',
            content='<h2>Refund Policy</h2><p>Please update this content from the admin panel.</p>',
            template='legal.html',
            active=True,
            show_in_nav=False
        )
        db.session.add(page)
        db.session.commit()
    
    return render_template('legal.html', page=page)

@app.route('/data-protection')
def data_protection():
    """Render Data Protection page"""
    page = Page.query.filter_by(slug='data-protection', active=True).first()
    if not page:
        page = Page(
            slug='data-protection',
            title='Data Protection',
            meta_title='Data Protection - ' + get_site_settings().site_name,
            meta_description='How we protect your data and comply with regulations.',
            content='<h2>Data Protection</h2><p>Please update this content from the admin panel.</p>',
            template='legal.html',
            active=True,
            show_in_nav=False
        )
        db.session.add(page)
        db.session.commit()
    
    return render_template('legal.html', page=page)

@app.route('/acceptable-use')
def acceptable_use():
    """Render Acceptable Use Policy page"""
    page = Page.query.filter_by(slug='acceptable-use', active=True).first()
    if not page:
        page = Page(
            slug='acceptable-use',
            title='Acceptable Use Policy',
            meta_title='Acceptable Use Policy - ' + get_site_settings().site_name,
            meta_description='Guidelines for acceptable use of our services.',
            content='<h2>Acceptable Use Policy</h2><p>Please update this content from the admin panel.</p>',
            template='legal.html',
            active=True,
            show_in_nav=False
        )
        db.session.add(page)
        db.session.commit()
    
    return render_template('legal.html', page=page)

@app.route('/admin/legal-pages')
@login_required
def admin_legal_pages():
    """Quick access to edit all legal pages"""
    legal_slugs = ['privacy-policy', 'terms-conditions', 'cookie-policy', 
                   'refund-policy', 'data-protection', 'acceptable-use']
    pages = Page.query.filter(Page.slug.in_(legal_slugs)).all()
    
    # Create missing legal pages
    existing_slugs = [p.slug for p in pages]
    for slug in legal_slugs:
        if slug not in existing_slugs:
            title = slug.replace('-', ' ').title()
            page = Page(
                slug=slug,
                title=title,
                meta_title=f'{title} - {get_site_settings().site_name}',
                meta_description=f'{title} for {get_site_settings().site_name}',
                content=f'<h2>{title}</h2><p>Please update this content.</p>',
                template='legal.html',
                active=True,
                show_in_nav=False
            )
            db.session.add(page)
    
    db.session.commit()
    pages = Page.query.filter(Page.slug.in_(legal_slugs)).all()
    
    return render_template('admin/legal_pages.html', pages=pages)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        # Fix: Explicit check with early returns for type narrowing
        if not admin:
            flash('Invalid credentials', 'error')
            return render_template('admin/login.html')
        
        if not admin.password:
            flash('Invalid credentials', 'error')
            return render_template('admin/login.html')
        
        if check_password_hash(admin.password, password or ""):
            session.permanent = True  
            session['admin_id'] = admin.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'employees': Employee.query.count(),
        'pages': Page.query.count(),
        'careers': Career.query.count(),
        'contacts': ContactSubmission.query.filter_by(read=False).count(),
        'partners': Partner.query.count(),
        'features': Feature.query.count()
    }
    
    # Get recent activity (last 10 events)
    recent_activity = []
    
    # Recent contact submissions
    recent_contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).limit(3).all()
    for contact in recent_contacts:
        time_diff = datetime.utcnow() - contact.created_at
        if time_diff.total_seconds() < 3600:
            time_ago = f"{int(time_diff.total_seconds() / 60)}m ago"
        elif time_diff.total_seconds() < 86400:
            time_ago = f"{int(time_diff.total_seconds() / 3600)}h ago"
        else:
            time_ago = f"{int(time_diff.total_seconds() / 86400)}d ago"
            
        recent_activity.append({
            'icon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>',
            'title': 'New Contact Form Submission',
            'description': f'{contact.first_name} {contact.last_name} sent an inquiry',
            'time_ago': time_ago
        })
    
    # Recent page updates
    recent_pages = Page.query.order_by(Page.updated_at.desc()).limit(2).all()
    for page in recent_pages:
        time_diff = datetime.utcnow() - page.updated_at
        if time_diff.total_seconds() < 3600:
            time_ago = f"{int(time_diff.total_seconds() / 60)}m ago"
        elif time_diff.total_seconds() < 86400:
            time_ago = f"{int(time_diff.total_seconds() / 3600)}h ago"
        else:
            time_ago = f"{int(time_diff.total_seconds() / 86400)}d ago"
            
        recent_activity.append({
            'icon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',
            'title': 'Page Updated',
            'description': f'{page.title} content was modified',
            'time_ago': time_ago
        })
    
    # Recent employees
    recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(2).all()
    for emp in recent_employees:
        time_diff = datetime.utcnow() - emp.created_at
        if time_diff.total_seconds() < 3600:
            time_ago = f"{int(time_diff.total_seconds() / 60)}m ago"
        elif time_diff.total_seconds() < 86400:
            time_ago = f"{int(time_diff.total_seconds() / 3600)}h ago"
        else:
            time_ago = f"{int(time_diff.total_seconds() / 86400)}d ago"
            
        recent_activity.append({
            'icon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>',
            'title': 'New Team Member Added',
            'description': f'{emp.name} was added to the {emp.department} team',
            'time_ago': time_ago
        })
    
    # Recent careers
    recent_careers = Career.query.order_by(Career.created_at.desc()).limit(2).all()
    for career in recent_careers:
        time_diff = datetime.utcnow() - career.created_at
        if time_diff.total_seconds() < 3600:
            time_ago = f"{int(time_diff.total_seconds() / 60)}m ago"
        elif time_diff.total_seconds() < 86400:
            time_ago = f"{int(time_diff.total_seconds() / 3600)}h ago"
        else:
            time_ago = f"{int(time_diff.total_seconds() / 86400)}d ago"
            
        recent_activity.append({
            'icon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
            'title': 'Job Posting Published',
            'description': f'{career.title} position is now live',
            'time_ago': time_ago
        })
    
    # Sort by most recent
    recent_activity.sort(key=lambda x: x['time_ago'])
    recent_activity = recent_activity[:10]  # Limit to 10 items
    
    return render_template('admin/dashboard.html', stats=stats, recent_activity=recent_activity)

@app.route('/admin/hero-sections')
@login_required
def admin_hero_sections():
    """List all hero sections"""
    heroes = HeroSection.query.all()
    return render_template('admin/hero_sections.html', heroes=heroes)

@app.route('/admin/hero-sections/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_hero_edit(id):
    """Edit hero section"""
    hero = HeroSection.query.get_or_404(id)
    
    if request.method == 'POST':
        # Basic fields
        hero.badge_text = request.form.get('badge_text')
        hero.badge_icon_type = request.form.get('badge_icon_type', 'none')
        
        # Handle badge icon content based on type
        if hero.badge_icon_type == 'emoji':
            hero.badge_icon_content = request.form.get('badge_icon_emoji', '')
        elif hero.badge_icon_type == 'svg':
            hero.badge_icon_content = request.form.get('badge_icon_svg', '')
        elif hero.badge_icon_type == 'image':
            # Handle image upload
            if 'badge_icon_image' in request.files:
                image = request.files['badge_icon_image']
                if image and image.filename:
                    image_path = save_image(image, 'heroes')
                    if image_path:
                        hero.badge_icon_content = image_path
        
        # Title fields
        hero.title_line1 = request.form.get('title_line1')
        hero.title_line2 = request.form.get('title_line2')
        hero.title_style = request.form.get('title_style', 'gradient')
        
        # Subtitle
        hero.subtitle = request.form.get('subtitle')
        
        # CTA fields
        hero.cta_text = request.form.get('cta_text')
        hero.cta_link = request.form.get('cta_link')
        hero.cta_style = request.form.get('cta_style', 'solid')
        
        # Background fields
        hero.background_type = request.form.get('background_type', 'particles')
        hero.background_overlay_opacity = int(request.form.get('background_overlay_opacity', 80))
        
        if hero.background_type == 'image':
            if 'background_image' in request.files:
                bg_image = request.files['background_image']
                if bg_image and bg_image.filename:
                    bg_path = save_image(bg_image, 'heroes')
                    if bg_path:
                        hero.background_image_path = bg_path
        elif hero.background_type == 'video':
            hero.background_video_url = request.form.get('background_video_url', '')
        
        # Layout fields
        hero.text_alignment = request.form.get('text_alignment', 'center')
        hero.min_height = request.form.get('min_height', '100vh')
        
        # Status
        hero.active = request.form.get('active') == 'on'
        
        hero.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Hero section for {hero.page} page updated successfully!', 'success')
        return redirect(url_for('admin_hero_sections'))
    
    return render_template('admin/hero_form.html', hero=hero)

@app.route('/admin/hero-sections/toggle/<int:id>')
@login_required
def admin_hero_toggle(id):
    """Toggle hero section active status"""
    hero = HeroSection.query.get_or_404(id)
    hero.active = not hero.active
    db.session.commit()
    status = 'activated' if hero.active else 'deactivated'
    flash(f'Hero section for {hero.page} page {status}', 'success')
    return redirect(url_for('admin_hero_sections'))
@app.route('/admin/stats')
@login_required
def admin_stats():
    stats = StatCard.query.order_by(StatCard.page, StatCard.order).all()
    return render_template('admin/stats.html', stats=stats)

@app.route('/admin/stats/add', methods=['GET', 'POST'])
@login_required
def admin_stat_add():
    if request.method == 'POST':
        stat = StatCard(
            page=request.form.get('page'),
            number=request.form.get('number'),
            label_line1=request.form.get('label_line1'),
            label_line2=request.form.get('label_line2', ''),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        db.session.add(stat)
        db.session.commit()
        flash('Stat added successfully', 'success')
        return redirect(url_for('admin_stats'))
    
    return render_template('admin/stat_form.html', stat=None)

@app.route('/admin/stats/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_stat_edit(id):
    stat = StatCard.query.get_or_404(id)
    
    if request.method == 'POST':
        stat.page = request.form.get('page')
        stat.number = request.form.get('number')
        stat.label_line1 = request.form.get('label_line1')
        stat.label_line2 = request.form.get('label_line2', '')
        stat.order = int(request.form.get('order', 0))
        stat.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Stat updated successfully', 'success')
        return redirect(url_for('admin_stats'))
    
    return render_template('admin/stat_form.html', stat=stat)

@app.route('/admin/stats/delete/<int:id>')
@login_required
def admin_stat_delete(id):
    stat = StatCard.query.get_or_404(id)
    db.session.delete(stat)
    db.session.commit()
    flash('Stat deleted successfully', 'success')
    return redirect(url_for('admin_stats'))

@app.route('/admin/features')
@login_required
def admin_features():
    features = Feature.query.order_by(Feature.order).all()
    return render_template('admin/features.html', features=features)

@app.route('/admin/features/add', methods=['GET', 'POST'])
@login_required
def admin_feature_add():
    if request.method == 'POST':
        # Get icon text (emoji or character)
        icon_text = request.form.get('icon_text', '⚡')
        
        feature = Feature(
            icon=icon_text if icon_text else '⚡',
            title=request.form.get('title'),
            description=request.form.get('description'),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        
        # Handle icon image upload
        if 'icon_image' in request.files:
            icon_file = request.files['icon_image']
            if icon_file and icon_file.filename:
                # Create features folder if it doesn't exist
                features_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'features')
                os.makedirs(features_folder, exist_ok=True)
                
                icon_path = save_image(icon_file, 'features')
                if icon_path:
                    feature.icon_path = icon_path
        
        db.session.add(feature)
        db.session.commit()
        flash('Feature added successfully', 'success')
        return redirect(url_for('admin_features'))
    
    return render_template('admin/feature_form.html', feature=None)

@app.route('/admin/features/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_feature_edit(id):
    feature = Feature.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get icon text (emoji or character)
        icon_text = request.form.get('icon_text', '⚡')
        feature.icon = icon_text if icon_text else '⚡'
        
        feature.title = request.form.get('title')
        feature.description = request.form.get('description')
        feature.order = int(request.form.get('order', 0))
        feature.active = request.form.get('active') == 'on'
        
        # Handle icon image upload
        if 'icon_image' in request.files:
            icon_file = request.files['icon_image']
            if icon_file and icon_file.filename:
                # Create features folder if it doesn't exist
                features_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'features')
                os.makedirs(features_folder, exist_ok=True)
                
                icon_path = save_image(icon_file, 'features')
                if icon_path:
                    feature.icon_path = icon_path
        
        db.session.commit()
        flash('Feature updated successfully', 'success')
        return redirect(url_for('admin_features'))
    
    return render_template('admin/feature_form.html', feature=feature)

@app.route('/admin/features/delete/<int:id>')
@login_required
def admin_feature_delete(id):
    feature = Feature.query.get_or_404(id)
    db.session.delete(feature)
    db.session.commit()
    flash('Feature deleted successfully', 'success')
    return redirect(url_for('admin_features'))

@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.order).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/testimonials/add', methods=['GET', 'POST'])
@login_required
def admin_testimonial_add():
    if request.method == 'POST':
        testimonial = Testimonial(
            rating=int(request.form.get('rating', 5)),
            text=request.form.get('text'),
            author_name=request.form.get('author_name'),
            author_title=request.form.get('author_title'),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        
        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                # Create testimonials folder if it doesn't exist
                testimonials_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'testimonials')
                os.makedirs(testimonials_folder, exist_ok=True)
                
                image_path = save_image(image, 'testimonials')
                if image_path:
                    testimonial.image_path = image_path
        
        db.session.add(testimonial)
        db.session.commit()
        flash('Testimonial added successfully', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin/testimonial_form.html', testimonial=None)

@app.route('/admin/testimonials/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_testimonial_edit(id):
    testimonial = Testimonial.query.get_or_404(id)
    
    if request.method == 'POST':
        testimonial.rating = int(request.form.get('rating', 5))
        testimonial.text = request.form.get('text')
        testimonial.author_name = request.form.get('author_name')
        testimonial.author_title = request.form.get('author_title')
        testimonial.order = int(request.form.get('order', 0))
        testimonial.active = request.form.get('active') == 'on'
        
        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                # Create testimonials folder if it doesn't exist
                testimonials_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'testimonials')
                os.makedirs(testimonials_folder, exist_ok=True)
                
                image_path = save_image(image, 'testimonials')
                if image_path:
                    testimonial.image_path = image_path
        
        db.session.commit()
        flash('Testimonial updated successfully', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin/testimonial_form.html', testimonial=testimonial)

@app.route('/admin/testimonials/delete/<int:id>')
@login_required
def admin_testimonial_delete(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial deleted successfully', 'success')
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/hubs')
@login_required
def admin_hubs():
    hubs = GlobalHub.query.order_by(GlobalHub.order).all()
    return render_template('admin/hubs.html', hubs=hubs)

@app.route('/admin/hubs/add', methods=['GET', 'POST'])
@login_required
def admin_hub_add():
    if request.method == 'POST':
        hub = GlobalHub(
            country=request.form.get('country'),
            flag=request.form.get('flag'),  # This was missing!
            city=request.form.get('city'),
            address=request.form.get('address'),
            maps_link=request.form.get('maps_link', '#'),
            is_featured=request.form.get('is_featured') == 'on',
            is_coming_soon=request.form.get('is_coming_soon') == 'on',
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        db.session.add(hub)
        db.session.commit()
        flash('Hub added successfully', 'success')
        return redirect(url_for('admin_hubs'))
    
    return render_template('admin/hub_form.html', hub=None)

@app.route('/admin/hubs/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_hub_edit(id):
    hub = GlobalHub.query.get_or_404(id)
    
    if request.method == 'POST':
        hub.country = request.form.get('country')
        hub.flag = request.form.get('flag')  
        hub.city = request.form.get('city')
        hub.address = request.form.get('address')
        hub.maps_link = request.form.get('maps_link', '#')
        hub.is_featured = request.form.get('is_featured') == 'on'
        hub.is_coming_soon = request.form.get('is_coming_soon') == 'on'
        hub.order = int(request.form.get('order', 0))
        hub.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Hub updated successfully', 'success')
        return redirect(url_for('admin_hubs'))
    
    return render_template('admin/hub_form.html', hub=hub)

@app.route('/admin/hubs/delete/<int:id>')
@login_required
def admin_hub_delete(id):
    hub = GlobalHub.query.get_or_404(id)
    db.session.delete(hub)
    db.session.commit()
    flash('Hub deleted successfully', 'success')
    return redirect(url_for('admin_hubs'))

@app.route('/admin/investors')
@login_required
def admin_investors():
    investors = Investor.query.order_by(Investor.order).all()
    return render_template('admin/investors.html', investors=investors)

@app.route('/admin/investors/add', methods=['GET', 'POST'])
@login_required
def admin_investor_add():
    if request.method == 'POST':
        investor = Investor(
            name=request.form.get('name'),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                logo_path = save_image(logo, 'logos')
                if logo_path:
                    investor.logo_path = logo_path
        
        db.session.add(investor)
        db.session.commit()
        flash('Investor added successfully', 'success')
        return redirect(url_for('admin_investors'))
    
    return render_template('admin/investor_form.html', investor=None)

@app.route('/admin/investors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_investor_edit(id):
    investor = Investor.query.get_or_404(id)
    
    if request.method == 'POST':
        investor.name = request.form.get('name')
        investor.order = int(request.form.get('order', 0))
        investor.active = request.form.get('active') == 'on'
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                logo_path = save_image(logo, 'logos')
                if logo_path:
                    investor.logo_path = logo_path
        
        db.session.commit()
        flash('Investor updated successfully', 'success')
        return redirect(url_for('admin_investors'))
    
    return render_template('admin/investor_form.html', investor=investor)

@app.route('/admin/investors/delete/<int:id>')
@login_required
def admin_investor_delete(id):
    investor = Investor.query.get_or_404(id)
    db.session.delete(investor)
    db.session.commit()
    flash('Investor deleted successfully', 'success')
    return redirect(url_for('admin_investors'))

@app.route('/admin/formula')
@login_required
def admin_formula():
    items = FormulaItem.query.order_by(FormulaItem.step_number).all()
    return render_template('admin/formula.html', formula_items=items)

@app.route('/admin/formula/add', methods=['GET', 'POST'])
@login_required
def admin_formula_add():
    if request.method == 'POST':
        # Get the highest step_number and increment
        max_step = db.session.query(db.func.max(FormulaItem.step_number)).scalar() or 0
        
        item = FormulaItem(
            step_number=max_step + 1,
            title=request.form.get('title'),
            description=request.form.get('description'),
            active=request.form.get('active') == 'on'
        )
        db.session.add(item)
        db.session.commit()
        flash('Formula step added successfully', 'success')
        return redirect(url_for('admin_formula'))
    
    return render_template('admin/formula_form.html', item=None)

@app.route('/admin/formula/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_formula_edit(id):
    item = FormulaItem.query.get_or_404(id)
    
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        item.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Formula step updated successfully', 'success')
        return redirect(url_for('admin_formula'))
    
    return render_template('admin/formula_form.html', item=item)

@app.route('/admin/formula/delete/<int:id>', methods=['POST'])
@login_required
def admin_formula_delete(id):
    item = FormulaItem.query.get_or_404(id)
    deleted_step = item.step_number
    
    db.session.delete(item)
    
    # Renumber remaining steps
    items_to_renumber = FormulaItem.query.filter(
        FormulaItem.step_number > deleted_step
    ).all()
    
    for item in items_to_renumber:
        item.step_number -= 1
    
    db.session.commit()
    flash('Formula step deleted successfully', 'success')
    return redirect(url_for('admin_formula'))

@app.route('/admin/formula/reorder', methods=['POST'])
@login_required
def admin_formula_reorder():
    """API endpoint for drag-and-drop reordering"""
    data = request.get_json()
    order_list = data.get('order', [])
    
    for index, item_id in enumerate(order_list, start=1):
        item = FormulaItem.query.get(item_id)
        if item:
            item.step_number = index
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/formula/toggle/<int:id>', methods=['POST'])
@login_required
def admin_formula_toggle(id):
    """API endpoint for quick toggle active status"""
    item = FormulaItem.query.get_or_404(id)
    item.active = not item.active
    db.session.commit()
    return jsonify({'success': True, 'active': item.active})

@app.route('/admin/partners')
@login_required
def admin_partners():
    partners = Partner.query.order_by(Partner.order).all()
    return render_template('admin/partners.html', partners=partners)

@app.route('/admin/partners/add', methods=['GET', 'POST'])
@login_required
def admin_partner_add():
    if request.method == 'POST':
        partner = Partner(
            name=request.form.get('name'),
            website=request.form.get('website', ''),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                logo_path = save_image(logo, 'partners')
                if logo_path:
                    partner.logo_path = logo_path
        
        db.session.add(partner)
        db.session.commit()
        flash('Partner added successfully', 'success')
        return redirect(url_for('admin_partners'))
    
    return render_template('admin/partner_form.html', partner=None)

@app.route('/admin/partners/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_partner_edit(id):
    partner = Partner.query.get_or_404(id)
    
    if request.method == 'POST':
        partner.name = request.form.get('name')
        partner.website = request.form.get('website', '')
        partner.order = int(request.form.get('order', 0))
        partner.active = request.form.get('active') == 'on'
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                logo_path = save_image(logo, 'partners')
                if logo_path:
                    partner.logo_path = logo_path
        
        db.session.commit()
        flash('Partner updated successfully', 'success')
        return redirect(url_for('admin_partners'))
    
    return render_template('admin/partner_form.html', partner=partner)

@app.route('/admin/partners/delete/<int:id>')
@login_required
def admin_partner_delete(id):
    partner = Partner.query.get_or_404(id)
    db.session.delete(partner)
    db.session.commit()
    flash('Partner deleted successfully', 'success')
    return redirect(url_for('admin_partners'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = get_site_settings()
    if request.method == 'POST':
        settings.site_name = request.form.get('site_name')
        settings.meta_title = request.form.get('meta_title')
        settings.meta_description = request.form.get('meta_description')
        settings.meta_keywords = request.form.get('meta_keywords')
        settings.footer_text = request.form.get('footer_text')
        settings.contact_email = request.form.get('contact_email')
        settings.contact_phone = request.form.get('contact_phone')
        settings.address = request.form.get('address')
        settings.social_instagram = request.form.get('social_instagram')
        settings.social_linkedin = request.form.get('social_linkedin')
        settings.social_twitter = request.form.get('social_twitter')
        settings.social_facebook = request.form.get('social_facebook')
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                logo_path = save_image(logo, 'logos')
                if logo_path:
                    settings.logo_path = logo_path
        
        if 'favicon' in request.files:
            favicon = request.files['favicon']
            if favicon and favicon.filename:
                favicon_path = save_image(favicon, 'logos')
                if favicon_path:
                    settings.favicon_path = favicon_path
        
        db.session.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/employees', methods=['GET'])
@login_required
def admin_employees():
    employees = Employee.query.order_by(Employee.order).all()
    
    # Calculate leadership count
    leadership_pattern = re.compile(r'CEO|CTO|CFO|Director|Head|VP|President|Founder', re.IGNORECASE)
    leadership_count = sum(1 for emp in employees if leadership_pattern.search(emp.designation))
    
    return render_template('admin/employees.html', 
                         employees=employees,
                         leadership_count=leadership_count)
    
@app.route('/admin/employee/add', methods=['GET', 'POST'])
@login_required
def admin_employee_add():
    if request.method == 'POST':
        name = request.form.get('name')
        designation = request.form.get('designation')
        gender = request.form.get('gender')
        bio = request.form.get('bio')
        order = int(request.form.get('order', 0))
        active = 'active' in request.form
        image_url = request.form.get('image_url', '').strip()
        
        image_path = None
        
        # Priority: Image URL > File Upload
        if image_url:
            # Store URL directly in image_path
            image_path = image_url
        elif 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                image_path = f'uploads/{unique_filename}'
        
        employee = Employee(
            name=name,
            designation=designation,
            gender=gender,
            bio=bio,
            image_path=image_path,
            order=order,
            active=active
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash('Team member added successfully!', 'success')
        return redirect(url_for('admin_employees'))
    
    return render_template('admin/employee_form.html')

@app.route('/admin/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_employee_edit(id):
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.designation = request.form.get('designation')
        employee.gender = request.form.get('gender')
        employee.bio = request.form.get('bio')
        employee.order = int(request.form.get('order', 0))
        employee.active = 'active' in request.form
        image_url = request.form.get('image_url', '').strip()
        
        # Priority: Image URL > File Upload > Keep existing
        if image_url:
            # Delete old file if it was a local upload (not a URL)
            if employee.image_path and not employee.image_path.startswith(('http://', 'https://')):
                old_file = os.path.join('static', employee.image_path)
                if os.path.exists(old_file):
                    os.remove(old_file)
            employee.image_path = image_url
        elif 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Delete old file if it was a local upload
                if employee.image_path and not employee.image_path.startswith(('http://', 'https://')):
                    old_file = os.path.join('static', employee.image_path)
                    if os.path.exists(old_file):
                        os.remove(old_file)
                
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                employee.image_path = f'uploads/{unique_filename}'
        
        db.session.commit()
        flash('Team member updated successfully!', 'success')
        return redirect(url_for('admin_employees'))
    
    return render_template('admin/employee_form.html', employee=employee)

@app.route('/admin/employees/bulk-action', methods=['POST'])
@login_required
def admin_employees_bulk_action():
    """Handle bulk operations like activate/deactivate multiple employees"""
    action = request.form.get('action')
    employee_ids = request.form.getlist('employee_ids')
    
    if not employee_ids:
        flash('No employees selected', 'error')
        return redirect(url_for('admin_employees'))
    
    employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
    
    if action == 'activate':
        for emp in employees:
            emp.active = True
        flash(f'{len(employees)} employee(s) activated', 'success')
    elif action == 'deactivate':
        for emp in employees:
            emp.active = False
        flash(f'{len(employees)} employee(s) deactivated', 'success')
    elif action == 'delete':
        for emp in employees:
            db.session.delete(emp)
        flash(f'{len(employees)} employee(s) deleted', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_employees'))

@app.route('/admin/employees/delete/<int:id>')
@login_required
def admin_employee_delete(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully', 'success')
    return redirect(url_for('admin_employees'))

@app.route('/admin/api/employee-stats')
@login_required
def admin_employee_stats():
    """API endpoint for employee statistics"""
    stats = {
        'total': Employee.query.count(),
        'active': Employee.query.filter_by(active=True).count(),
        'by_department': {
            'leadership': Employee.query.filter_by(department='leadership').count(),
            'engineering': Employee.query.filter_by(department='engineering').count(),
            'design': Employee.query.filter_by(department='design').count(),
            'operations': Employee.query.filter_by(department='operations').count(),
            'other': Employee.query.filter_by(department='other').count(),
        },
        'by_gender': {
            'male': Employee.query.filter_by(gender='male').count(),
            'female': Employee.query.filter_by(gender='female').count(),
            'other': Employee.query.filter_by(gender='other').count(),
        }
    }
    return jsonify(stats)

@app.route('/admin/pages', methods=['GET'])
@login_required
def admin_pages():
    """List all pages"""
    pages = Page.query.order_by(Page.order).all()
    return render_template('admin/pages.html', pages=pages)

@app.route('/admin/pages/add', methods=['GET', 'POST'])
@login_required
def admin_page_add():
    """Add a new page"""
    if request.method == 'POST':
        # Generate slug from title if not provided
        slug = request.form.get('slug', '').strip()
        if not slug:
            title = request.form.get('title', '')
            slug = title.lower().replace(' ', '-').replace('_', '-')
            # Remove special characters
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Check if slug already exists
        existing_page = Page.query.filter_by(slug=slug).first()
        if existing_page:
            flash(f'A page with slug "{slug}" already exists!', 'error')
            return render_template('admin/page_form.html', page=None)
        
        page = Page(
            slug=slug,
            title=request.form.get('title'),
            meta_title=request.form.get('meta_title', ''),
            meta_description=request.form.get('meta_description', ''),
            content=request.form.get('content', ''),
            template=request.form.get('template', 'page.html'),
            active=request.form.get('active') == 'on',
            show_in_nav=request.form.get('show_in_nav') == 'on',
            order=int(request.form.get('order', 0))
        )
        
        db.session.add(page)
        db.session.commit()
        flash('Page created successfully!', 'success')
        return redirect(url_for('admin_pages'))
    
    return render_template('admin/page_form.html', page=None)

@app.route('/admin/pages/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_page_edit(id):
    """Edit an existing page"""
    page = Page.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get slug and check for duplicates (excluding current page)
        slug = request.form.get('slug', '').strip()
        if not slug:
            title = request.form.get('title', '')
            slug = title.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Check if slug exists for another page
        existing_page = Page.query.filter(Page.slug == slug, Page.id != id).first()
        if existing_page:
            flash(f'A page with slug "{slug}" already exists!', 'error')
            return render_template('admin/page_form.html', page=page)
        
        page.slug = slug
        page.title = request.form.get('title')
        page.meta_title = request.form.get('meta_title', '')
        page.meta_description = request.form.get('meta_description', '')
        page.content = request.form.get('content', '')
        page.template = request.form.get('template', 'page.html')
        page.active = request.form.get('active') == 'on'
        page.show_in_nav = request.form.get('show_in_nav') == 'on'
        page.order = int(request.form.get('order', 0))
        page.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Page updated successfully!', 'success')
        return redirect(url_for('admin_pages'))
    
    return render_template('admin/page_form.html', page=page)

@app.route('/admin/pages/delete/<int:id>')
@login_required
def admin_page_delete(id):
    """Delete a page"""
    page = Page.query.get_or_404(id)
    
    # Prevent deletion of system pages
    protected_slugs = ['home', 'about', 'privacy-policy', 'terms-conditions']
    if page.slug in protected_slugs:
        flash(f'Cannot delete system page "{page.title}"', 'error')
        return redirect(url_for('admin_pages'))
    
    db.session.delete(page)
    db.session.commit()
    flash('Page deleted successfully!', 'success')
    return redirect(url_for('admin_pages'))

@app.route('/admin/pages/toggle/<int:id>/<field>')
@login_required
def admin_page_toggle(id, field):
    """Toggle page fields (active, show_in_nav)"""
    page = Page.query.get_or_404(id)
    
    if field == 'active':
        page.active = not page.active
        status = 'activated' if page.active else 'deactivated'
    elif field == 'show_in_nav':
        page.show_in_nav = not page.show_in_nav
        status = 'shown in navigation' if page.show_in_nav else 'hidden from navigation'
    else:
        flash('Invalid field', 'error')
        return redirect(url_for('admin_pages'))
    
    db.session.commit()
    flash(f'Page "{page.title}" {status}', 'success')
    return redirect(url_for('admin_pages'))

@app.route('/admin/pages/reorder', methods=['POST'])
@login_required
def admin_pages_reorder():
    """Reorder pages"""
    try:
        page_ids = request.json.get('page_ids', [])
        for index, page_id in enumerate(page_ids):
            page = Page.query.get(page_id)
            if page:
                page.order = index
        db.session.commit()
        return jsonify({'success': True, 'message': 'Pages reordered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/admin/pages/bulk-action', methods=['POST'])
@login_required
def admin_pages_bulk_action():
    """Handle bulk operations on pages"""
    action = request.form.get('action')
    page_ids = request.form.getlist('page_ids')
    
    if not page_ids:
        flash('No pages selected', 'error')
        return redirect(url_for('admin_pages'))
    
    pages = Page.query.filter(Page.id.in_(page_ids)).all()
    protected_slugs = ['home', 'about', 'privacy-policy', 'terms-conditions']
    
    if action == 'activate':
        for page in pages:
            page.active = True
        flash(f'{len(pages)} page(s) activated', 'success')
    elif action == 'deactivate':
        for page in pages:
            page.active = False
        flash(f'{len(pages)} page(s) deactivated', 'success')
    elif action == 'show_nav':
        for page in pages:
            page.show_in_nav = True
        flash(f'{len(pages)} page(s) added to navigation', 'success')
    elif action == 'hide_nav':
        for page in pages:
            page.show_in_nav = False
        flash(f'{len(pages)} page(s) hidden from navigation', 'success')
    elif action == 'delete':
        # Filter out protected pages
        deletable_pages = [p for p in pages if p.slug not in protected_slugs]
        protected_count = len(pages) - len(deletable_pages)
        
        for page in deletable_pages:
            db.session.delete(page)
        
        message = f'{len(deletable_pages)} page(s) deleted'
        if protected_count > 0:
            message += f' ({protected_count} system page(s) skipped)'
        flash(message, 'success')
    
    db.session.commit()
    return redirect(url_for('admin_pages'))

# Dynamic page route handler
@app.route('/<slug>')
def dynamic_page(slug):
    """Render dynamic pages based on slug"""
    page = Page.query.filter_by(slug=slug, active=True).first_or_404()
    
    # Use specified template or default
    template = page.template if page.template else 'page.html'
    
    return render_template(template, page=page)

@app.route('/admin/careers', methods=['GET'])
@login_required
def admin_careers():
    # Get filter parameters
    department = request.args.get('department', '')
    job_type = request.args.get('job_type', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Career.query
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    if job_type:
        query = query.filter_by(job_type=job_type)
    if status == 'active':
        query = query.filter_by(active=True)
    elif status == 'inactive':
        query = query.filter_by(active=False)
    
    careers = query.order_by(Career.featured.desc(), Career.created_at.desc()).all()
    
    # Calculate statistics
    all_careers = Career.query.all()
    stats = {
        'total': len(all_careers),
        'active': sum(1 for c in all_careers if c.active),
        'by_department': {},
        'by_type': {}
    }
    
    # Count by department and type
    for career in all_careers:
        dept = career.department
        stats['by_department'][dept] = stats['by_department'].get(dept, 0) + 1
        
        job_type_val = career.job_type
        stats['by_type'][job_type_val] = stats['by_type'].get(job_type_val, 0) + 1
    
    return render_template('admin/careers.html', 
                         careers=careers,
                         stats=stats)

@app.route('/admin/careers/add', methods=['GET', 'POST'])
@login_required
def admin_career_add():
    if request.method == 'POST':
        career = Career(
            title=request.form.get('title'),
            department=request.form.get('department'),
            location=request.form.get('location'),
            job_type=request.form.get('job_type', 'Full-time'),
            experience_level=request.form.get('experience_level', 'Mid-level'),
            salary_range=request.form.get('salary_range', ''),
            description=request.form.get('description'),
            requirements=request.form.get('requirements', ''),
            responsibilities=request.form.get('responsibilities', ''),
            benefits=request.form.get('benefits', ''),
            skills=request.form.get('skills', ''),
            external_link=request.form.get('external_link', 'https://shramicintern.pythonanywhere.com/'),
            featured=request.form.get('featured') == 'on',
            remote_allowed=request.form.get('remote_allowed') == 'on',
            active=request.form.get('active') == 'on'
        )
        db.session.add(career)
        db.session.commit()
        flash('Career position added successfully!', 'success')
        return redirect(url_for('admin_careers'))
    
    return render_template('admin/career_form.html', career=None)

@app.route('/admin/careers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_career_edit(id):
    career = Career.query.get_or_404(id)
    
    if request.method == 'POST':
        career.title = request.form.get('title')
        career.department = request.form.get('department')
        career.location = request.form.get('location')
        career.job_type = request.form.get('job_type', 'Full-time')
        career.experience_level = request.form.get('experience_level', 'Mid-level')
        career.salary_range = request.form.get('salary_range', '')
        career.description = request.form.get('description')
        career.requirements = request.form.get('requirements', '')
        career.responsibilities = request.form.get('responsibilities', '')
        career.benefits = request.form.get('benefits', '')
        career.skills = request.form.get('skills', '')
        career.external_link = request.form.get('external_link', 'https://shramicintern.pythonanywhere.com/')
        career.featured = request.form.get('featured') == 'on'
        career.remote_allowed = request.form.get('remote_allowed') == 'on'
        career.active = request.form.get('active') == 'on'
        career.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Career position updated successfully!', 'success')
        return redirect(url_for('admin_careers'))
    
    return render_template('admin/career_form.html', career=career)

@app.route('/admin/careers/delete/<int:id>')
@login_required
def admin_career_delete(id):
    career = Career.query.get_or_404(id)
    db.session.delete(career)
    db.session.commit()
    flash('Career position deleted successfully!', 'success')
    return redirect(url_for('admin_careers'))

@app.route('/admin/careers/bulk-action', methods=['POST'])
@login_required
def admin_careers_bulk_action():
    """Handle bulk operations on career postings"""
    action = request.form.get('action')
    career_ids = request.form.getlist('career_ids')
    
    if not career_ids:
        flash('No positions selected', 'error')
        return redirect(url_for('admin_careers'))
    
    careers = Career.query.filter(Career.id.in_(career_ids)).all()
    
    if action == 'activate':
        for career in careers:
            career.active = True
        flash(f'{len(careers)} position(s) activated', 'success')
    elif action == 'deactivate':
        for career in careers:
            career.active = False
        flash(f'{len(careers)} position(s) deactivated', 'success')
    elif action == 'feature':
        for career in careers:
            career.featured = True
        flash(f'{len(careers)} position(s) marked as featured', 'success')
    elif action == 'unfeature':
        for career in careers:
            career.featured = False
        flash(f'{len(careers)} position(s) unfeatured', 'success')
    elif action == 'delete':
        for career in careers:
            db.session.delete(career)
        flash(f'{len(careers)} position(s) deleted', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_careers'))

@app.route('/admin/api/career-stats')
@login_required
def admin_career_stats():
    """API endpoint for career statistics"""
    careers = Career.query.all()
    
    stats = {
        'total': len(careers),
        'active': sum(1 for c in careers if c.active),
        'featured': sum(1 for c in careers if c.featured),
        'remote': sum(1 for c in careers if c.remote_allowed),
        'by_department': {},
        'by_type': {},
        'by_location': {},
        'by_experience': {}
    }
    
    for career in careers:
        # Department
        dept = career.department
        stats['by_department'][dept] = stats['by_department'].get(dept, 0) + 1
        
        # Job Type
        job_type = career.job_type
        stats['by_type'][job_type] = stats['by_type'].get(job_type, 0) + 1
        
        # Location
        location = career.location
        stats['by_location'][location] = stats['by_location'].get(location, 0) + 1
        
        # Experience Level
        exp = career.experience_level or 'Not specified'
        stats['by_experience'][exp] = stats['by_experience'].get(exp, 0) + 1
    
    return jsonify(stats)

@app.route('/admin/contacts')
@login_required
def admin_contacts():
    contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    return render_template('admin/contacts.html', contacts=contacts)

@app.route('/admin/contacts/mark-read/<int:id>')
@login_required
def admin_contact_mark_read(id):
    contact = ContactSubmission.query.get_or_404(id)
    contact.read = True
    db.session.commit()
    flash('Contact marked as read', 'success')
    return redirect(url_for('admin_contacts'))

@app.route('/admin/contacts/delete/<int:id>')
@login_required
def admin_contact_delete(id):
    contact = ContactSubmission.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact submission deleted successfully', 'success')
    return redirect(url_for('admin_contacts'))
# Replace your footer link routes with these corrected versions

@app.route('/admin/footer-links', methods=['GET', 'POST'])
@login_required
def admin_footer_links():
    if request.method == 'POST':
        link = FooterLink(
            category=request.form.get('category'),
            title=request.form.get('title'),
            url=request.form.get('url'),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        db.session.add(link)
        db.session.commit()
        flash('Footer link added successfully', 'success')
        return redirect(url_for('admin_footer_links'))
    
    links = FooterLink.query.order_by(FooterLink.category, FooterLink.order).all()
    
    # Get unique categories for display
    categories = db.session.query(FooterLink.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('admin/footer_links.html', links=links, categories=categories)

@app.route('/admin/footer-links/add', methods=['GET', 'POST'])
@login_required
def admin_footer_link_add():
    """Add new footer link"""
    if request.method == 'POST':
        link = FooterLink(
            category=request.form.get('category'),
            title=request.form.get('title'),
            url=request.form.get('url'),
            order=int(request.form.get('order', 0)),
            active=request.form.get('active') == 'on'
        )
        db.session.add(link)
        db.session.commit()
        flash('Footer link added successfully!', 'success')
        return redirect(url_for('admin_footer_links'))
    
    return render_template('admin/footer_link_form.html', link=None)

@app.route('/admin/footer-links/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_footer_link_edit(id):
    link = FooterLink.query.get_or_404(id)
    
    if request.method == 'POST':
        link.category = request.form.get('category')
        link.title = request.form.get('title')
        link.url = request.form.get('url')
        link.order = int(request.form.get('order', 0))
        link.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Footer link updated successfully', 'success')
        return redirect(url_for('admin_footer_links'))
    
    return render_template('admin/footer_link_form.html', link=link)

@app.route('/admin/footer-links/delete/<int:id>')
@login_required
def admin_footer_link_delete(id):
    link = FooterLink.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    flash('Footer link deleted successfully', 'success')
    return redirect(url_for('admin_footer_links'))

@app.route('/admin/footer-links/bulk-action', methods=['POST'])
@login_required
def admin_footer_links_bulk_action():
    """Handle bulk operations on footer links"""
    action = request.form.get('action')
    link_ids = request.form.getlist('link_ids')
    
    if not link_ids:
        flash('No links selected', 'error')
        return redirect(url_for('admin_footer_links'))
    
    links = FooterLink.query.filter(FooterLink.id.in_(link_ids)).all()
    
    if action == 'activate':
        for link in links:
            link.active = True
        flash(f'{len(links)} link(s) activated', 'success')
    elif action == 'deactivate':
        for link in links:
            link.active = False
        flash(f'{len(links)} link(s) deactivated', 'success')
    elif action == 'delete':
        for link in links:
            db.session.delete(link)
        flash(f'{len(links)} link(s) deleted', 'success')
    elif action == 'change_category':
        new_category = request.form.get('new_category')
        if new_category:
            for link in links:
                link.category = new_category
            flash(f'{len(links)} link(s) moved to {new_category}', 'success')
        else:
            flash('Please specify a category', 'error')
    
    db.session.commit()
    return redirect(url_for('admin_footer_links'))

@app.route('/admin/footer-links/reorder', methods=['POST'])
@login_required
def admin_footer_links_reorder():
    """Reorder footer links via AJAX"""
    try:
        link_ids = request.json.get('link_ids', [])
        for index, link_id in enumerate(link_ids):
            link = FooterLink.query.get(link_id)
            if link:
                link.order = index
        db.session.commit()
        return jsonify({'success': True, 'message': 'Links reordered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/admin/api/footer-stats')
@login_required
def admin_footer_stats():
    """API endpoint for footer link statistics"""
    links = FooterLink.query.all()
    
    stats = {
        'total': len(links),
        'active': sum(1 for link in links if link.active),
        'by_category': {}
    }
    
    for link in links:
        category = link.category
        if category not in stats['by_category']:
            stats['by_category'][category] = {'total': 0, 'active': 0}
        stats['by_category'][category]['total'] += 1
        if link.active:
            stats['by_category'][category]['active'] += 1
    
    return jsonify(stats)

@app.route('/admin/footer-links/toggle/<int:id>')
@login_required
def admin_footer_link_toggle(id):
    """Quick toggle active status"""
    link = FooterLink.query.get_or_404(id)
    link.active = not link.active
    db.session.commit()
    
    status = 'activated' if link.active else 'deactivated'
    flash(f'Link "{link.title}" {status}', 'success')
    return redirect(url_for('admin_footer_links'))

@app.route('/admin/footer-links/duplicate/<int:id>')
@login_required
def admin_footer_link_duplicate(id):
    """Duplicate a footer link"""
    original = FooterLink.query.get_or_404(id)
    
    duplicate = FooterLink(
        category=original.category,
        title=f"{original.title} (Copy)",
        url=original.url,
        order=original.order + 1,
        active=False
    )
    
    db.session.add(duplicate)
    db.session.commit()
    
    flash(f'Link duplicated successfully! Edit to customize.', 'success')
    return redirect(url_for('admin_footer_link_edit', id=duplicate.id))

@app.route('/admin/footer-links/export')
@login_required
def admin_footer_links_export():
    """Export footer links as JSON"""
    links = FooterLink.query.order_by(FooterLink.category, FooterLink.order).all()
    
    export_data = {
        'footer_links': [
            {
                'category': link.category,
                'title': link.title,
                'url': link.url,
                'order': link.order,
                'active': link.active
            }
            for link in links
        ],
        'export_date': datetime.utcnow().isoformat(),
        'total_links': len(links)
    }
    
    response = jsonify(export_data)
    response.headers['Content-Disposition'] = f'attachment; filename=footer_links_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/admin/footer-links/import', methods=['POST'])
@login_required
def admin_footer_links_import():
    """Import footer links from JSON"""
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin_footer_links'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_footer_links'))
    
    # Fix for Error 2: Check if filename exists before calling endswith
    if not file.filename or not file.filename.endswith('.json'):
        flash('Invalid file format. Please upload a JSON file.', 'error')
        return redirect(url_for('admin_footer_links'))
    
    try:
        # Fix for Error 1: Read file content properly
        file_content = file.read().decode('utf-8')
        data = json.loads(file_content)
        
        if 'footer_links' not in data:
            flash('Invalid file format. Missing footer_links data.', 'error')
            return redirect(url_for('admin_footer_links'))
        
        # Option to clear existing links
        clear_existing = request.form.get('clear_existing') == 'on'
        if clear_existing:
            FooterLink.query.delete()
        
        # Import new links
        imported_count = 0
        for link_data in data['footer_links']:
            link = FooterLink(
                category=link_data['category'],
                title=link_data['title'],
                url=link_data['url'],
                order=link_data.get('order', 0),
                active=link_data.get('active', True)
            )
            db.session.add(link)
            imported_count += 1
        
        db.session.commit()
        flash(f'Successfully imported {imported_count} footer links!', 'success')
        
    except json.JSONDecodeError:
        flash('Invalid JSON file', 'error')
    except Exception as e:
        flash(f'Error importing links: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin_footer_links'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
# Replace the bottom of your app.py (from init_db() onwards) with this:

def init_db():
    """Initialize database - only run locally or in specific deployment contexts"""
    with app.app_context():
        try:
            db.create_all()
            
            # Create default admin
            if not Admin.query.first():
                admin = Admin(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    email='admin@sharmic.com'
                )
                db.session.add(admin)
            
            # Create default hero sections
            if not HeroSection.query.filter_by(page='home').first():
                home_hero = HeroSection(
                    page='home',
                    badge_text='WELCOME TO SHARMIC',
                    title_line1='We Engineer Payments',
                    title_line2='for Global Scale',
                    subtitle='Trusted by leading enterprises worldwide. Simplify payment orchestration, boost conversions, reduce fraud, and deliver seamless customer experiences.',
                    cta_text='Get Started',
                    cta_link='/contact',
                    active=True
                )
                db.session.add(home_hero)
            
            if not HeroSection.query.filter_by(page='about').first():
                about_hero = HeroSection(
                    page='about',
                    badge_text='ABOUT US',
                    title_line1='We Engineer Payments',
                    title_line2='for Global Scale',
                    subtitle='Trusted by leading enterprises worldwide, SHARMIC simplifies payment orchestration and global coverage, boosts conversions, reduces fraud, and delivers seamless customer experiences.',
                    cta_text='Schedule a call',
                    cta_link='/contact',
                    active=True
                )
                db.session.add(about_hero)
            
            # Create default pages
            if not Page.query.filter_by(slug='home').first():
                home_page = Page(
                    slug='home',
                    title='Home',
                    meta_title='SHARMIC - Payment Solutions for Global Scale',
                    meta_description='We engineer payments for global scale',
                    template='index.html',
                    active=True,
                    show_in_nav=True,
                    order=1
                )
                db.session.add(home_page)
            
            if not Page.query.filter_by(slug='about').first():
                about_page = Page(
                    slug='about',
                    title='About Us',
                    meta_title='About SHARMIC - Our Story',
                    meta_description='Learn about SHARMIC and our mission',
                    template='about.html',
                    active=True,
                    show_in_nav=True,
                    order=2
                )
                db.session.add(about_page)
            
            legal_pages_data = [
                {
                    'slug': 'privacy-policy',
                    'title': 'Privacy Policy',
                    'content': '''<h2>1. Information We Collect</h2><p>We collect information that you provide directly to us...</p>'''
                },
                {
                    'slug': 'terms-conditions',
                    'title': 'Terms & Conditions',
                    'content': '''<h2>1. Acceptance of Terms</h2><p>By accessing and using our services...</p>'''
                },
                {
                    'slug': 'cookie-policy',
                    'title': 'Cookie Policy',
                    'content': '''<h2>What Are Cookies</h2><p>Cookies are small text files...</p>'''
                }
            ]
            
            for page_data in legal_pages_data:
                if not Page.query.filter_by(slug=page_data['slug']).first():
                    page = Page(
                        slug=page_data['slug'],
                        title=page_data['title'],
                        meta_title=f"{page_data['title']} - SHARMIC",
                        meta_description=f"Read our {page_data['title'].lower()}",
                        content=page_data['content'],
                        template='legal.html',
                        active=True,
                        show_in_nav=False,
                        order=100
                    )
                    db.session.add(page)
                    
            initialize_default_footer_links()
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Database initialization error: {e}")
            db.session.rollback()

# Initialize database tables on app start (but don't populate data on Vercel)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating tables: {e}")

# This is for running locally only
if __name__ == '__main__':
    # Only initialize data when running locally
    if os.environ.get('FLASK_ENV') != 'production':
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)