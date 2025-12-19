from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from functools import wraps
import hashlib
from datetime import datetime
import uuid
import os
import json
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here_change_this_in_production')

# Database configuration - supports both local SQLite and Vercel Postgres
if os.environ.get('POSTGRES_URL'):
    # Production: Use Vercel Postgres
    database_url = os.environ.get('POSTGRES_URL')
    # Fix for SQLAlchemy (postgres:// -> postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development: Use SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'shramic.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class ContactSubmission(db.Model):
    __tablename__ = 'contact_submissions'
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    admin_reply = db.Column(db.Text, nullable=True)
    reply_timestamp = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tracking_id': self.tracking_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'admin_reply': self.admin_reply,
            'reply_timestamp': self.reply_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.reply_timestamp else None
        }

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    read_time = db.Column(db.String(20))
    featured = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(500))
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text)

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    image = db.Column(db.String(500))
    rating = db.Column(db.Integer, default=5)
    testimonial = db.Column(db.Text, nullable=False)
    results = db.Column(db.Text)  # JSON string
    featured = db.Column(db.Boolean, default=False)
    date = db.Column(db.Date, default=datetime.utcnow)

class Statistic(db.Model):
    __tablename__ = 'statistics'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(50), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100))
    order = db.Column(db.Integer, default=0)

class VideoStory(db.Model):
    __tablename__ = 'video_stories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    youtube_url = db.Column(db.String(500))
    thumbnail = db.Column(db.String(500))
    duration = db.Column(db.String(20))
    views = db.Column(db.String(20))
    featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)

# Admin credentials
ADMIN_CREDENTIALS = {
    'username': 'Shramicadmin',
    'password_hash': '71873303a486338db55ba099625938a1267dba18b8ce68d76aba2a3354f8bba6'  
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def initialize_database():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()
        
        # Check if data already exists
        if Statistic.query.count() == 0:
            # Add sample statistics
            stats = [
                Statistic(value='50K+', label='Farmers Empowered', icon='fas fa-users', order=1),
                Statistic(value='40%', label='Average Yield Increase', icon='fas fa-chart-line', order=2),
                Statistic(value='₹2.5Cr', label='Additional Income Generated', icon='fas fa-rupee-sign', order=3),
                Statistic(value='95%', label='Satisfaction Rate', icon='fas fa-smile', order=4)
            ]
            db.session.add_all(stats)
            db.session.commit()
        
        if Testimonial.query.count() == 0:
            # Add sample testimonials
            testimonials = [
                Testimonial(
                    name='Rajesh Kumar',
                    location='Haryana',
                    image='https://i.pravatar.cc/200?img=12',
                    rating=5,
                    testimonial='Shramic Networks completely transformed how I manage my 20-acre wheat farm. The smart irrigation system they installed reduced my water usage by 35% while increasing my yield by 25%.',
                    results=json.dumps(['25% increase in crop yield', '35% reduction in water usage', '₹8 lakhs additional annual income']),
                    featured=True,
                    date=datetime(2025, 11, 15)
                ),
                Testimonial(
                    name='Priya Devi',
                    location='Punjab',
                    image='https://i.pravatar.cc/200?img=45',
                    rating=5,
                    testimonial='As a woman farmer, I faced many challenges accessing technology and markets. Shramic\'s training programs gave me confidence and their platform connected me directly with buyers.',
                    results=json.dumps(['Direct market access achieved', '45% better prices received', 'Became organic certified farmer']),
                    featured=True,
                    date=datetime(2025, 10, 28)
                ),
                Testimonial(
                    name='Suresh Patel',
                    location='Gujarat',
                    image='https://i.pravatar.cc/200?img=33',
                    rating=5,
                    testimonial='The soil testing and crop advisory services saved my cotton farm. I was using excessive fertilizers without knowing my soil\'s actual needs.',
                    results=json.dumps(['30% reduction in fertilizer costs', 'Improved soil fertility rating', 'Better cotton quality grades']),
                    featured=True,
                    date=datetime(2025, 9, 12)
                ),
                Testimonial(
                    name='Arun Singh',
                    location='Uttar Pradesh',
                    image='https://i.pravatar.cc/200?img=51',
                    rating=5,
                    testimonial='I was skeptical about technology at first, but Shramic\'s team patiently trained me and my family. The pest detection feature alone saved us from a potential 40% crop loss.',
                    results=json.dumps(['Prevented major crop loss', 'Family engaged in farming again', '50% faster issue resolution']),
                    featured=False,
                    date=datetime(2025, 8, 5)
                )
            ]
            db.session.add_all(testimonials)
            db.session.commit()
        
        if VideoStory.query.count() == 0:
            # Add sample video stories
            videos = [
                VideoStory(
                    title='From Traditional to Smart Farming',
                    description='See how Ramesh transformed his 50-acre farm using IoT sensors',
                    youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    thumbnail='https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                    duration='8:45',
                    views='125K',
                    featured=True,
                    order=1
                ),
                VideoStory(
                    title='Doubling Income in One Season',
                    description='Meena shares her journey from struggling to thriving farmer',
                    youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    thumbnail='https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                    duration='6:30',
                    views='98K',
                    featured=True,
                    order=2
                )
            ]
            db.session.add_all(videos)
            db.session.commit()
        
        if BlogPost.query.count() == 0:
            # Add sample blog posts
            blogs = [
                BlogPost(
                    title='How the Shramic Ecosystem is Transforming Rural Livelihoods',
                    slug='shramic-ecosystem-transforming-rural-livelihoods',
                    category='Shramic Krushi',
                    author='Dr. Anjali Sharma',
                    date=datetime(2025, 12, 10),
                    read_time='8 min read',
                    featured=True,
                    image='https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=800&h=500&fit=crop',
                    excerpt='Discover how Shramic Networks brings together farmers, workers, experts, and service providers onto a single digital platform.',
                    content='<h2>The Digital Bridge to Rural Prosperity</h2><p>In the heart of rural India, where traditional farming meets modern challenges, Shramic Networks is building something revolutionary...</p>'
                )
            ]
            db.session.add_all(blogs)
            db.session.commit()

# Public Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    filter_category = request.args.get('category', 'all')
    
    if filter_category == 'all':
        posts = BlogPost.query.order_by(BlogPost.date.desc()).all()
    else:
        posts = BlogPost.query.filter_by(category=filter_category).order_by(BlogPost.date.desc()).all()
    
    return render_template('blog.html', posts=posts, filter_category=filter_category)

@app.route('/blog/<slug>')
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug).first()
    if not post:
        flash('Blog post not found', 'error')
        return redirect(url_for('blog'))
    
    related_posts = BlogPost.query.filter(BlogPost.category == post.category, BlogPost.id != post.id).limit(3).all()
    recent_posts = BlogPost.query.filter(BlogPost.id != post.id).order_by(BlogPost.date.desc()).limit(4).all()
    
    return render_template('blog_detail.html', post=post, related_posts=related_posts, recent_posts=recent_posts)

@app.route('/testimonial')
def testimonial():
    stats = Statistic.query.order_by(Statistic.order).all()
    featured_testimonials = Testimonial.query.filter_by(featured=True).all()
    all_testimonials = Testimonial.query.order_by(Testimonial.date.desc()).all()
    featured_videos = VideoStory.query.filter_by(featured=True).order_by(VideoStory.order).all()
    
    # Parse JSON results for testimonials - check if it's a string first
    for t in all_testimonials:
        if t.results and isinstance(t.results, str):
            t.results = json.loads(t.results)
        elif not t.results:
            t.results = []
    
    for t in featured_testimonials:
        if t.results and isinstance(t.results, str):
            t.results = json.loads(t.results)
        elif not t.results:
            t.results = []
    
    return render_template('testimonial.html',
                         statistics=stats,
                         featured_testimonials=featured_testimonials,
                         all_testimonials=all_testimonials,
                         video_stories=featured_videos)

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        tracking_id = str(uuid.uuid4())[:8].upper()
        
        submission = ContactSubmission(
            tracking_id=tracking_id,
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            subject=request.form.get('subject'),
            message=request.form.get('message'),
            status='pending'
        )
        
        db.session.add(submission)
        db.session.commit()
        
        # Store tracking ID in session for this device
        session['user_tracking_id'] = tracking_id
        session['user_name'] = submission.name
        
        flash('Thank you for contacting us! Your tracking ID is: ' + tracking_id, 'success')
        return redirect(url_for('contact'))
    
    # Check if user has a tracking ID in session
    user_tracking_id = session.get('user_tracking_id')
    user_submission = None
    
    if user_tracking_id:
        # Fetch the latest submission for this tracking ID from database
        submission = ContactSubmission.query.filter_by(tracking_id=user_tracking_id).first()
        if submission:
            user_submission = submission.to_dict()
    
    return render_template('contact.html', user_submission=user_submission)

@app.route('/check-reply', methods=['POST'])
def check_reply():
    tracking_id = request.form.get('tracking_id', '').strip().upper()
    
    if not tracking_id:
        flash('Please enter your tracking ID', 'error')
        return redirect(url_for('contact'))
    
    submission = ContactSubmission.query.filter_by(tracking_id=tracking_id).first()
    
    if submission:
        # Store this tracking ID in session
        session['user_tracking_id'] = tracking_id
        session['user_name'] = submission.name
        
        if submission.admin_reply:
            flash('Reply found! Check below for admin response.', 'success')
        else:
            flash('Your inquiry is being processed. No reply yet.', 'info')
    else:
        flash('Invalid tracking ID. Please check and try again.', 'error')
    
    return redirect(url_for('contact'))

@app.route('/clear-session')
def clear_session():
    session.pop('user_tracking_id', None)
    session.pop('user_name', None)
    flash('Session cleared successfully', 'info')
    return redirect(url_for('contact'))

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if (username == ADMIN_CREDENTIALS['username'] and 
            hash_password(password) == ADMIN_CREDENTIALS['password_hash']):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_submissions = ContactSubmission.query.count()
    pending_count = ContactSubmission.query.filter_by(status='pending').count()
    replied_count = ContactSubmission.query.filter_by(status='replied').count()
    total_blogs = BlogPost.query.count()
    
    return render_template('admin_dashboard.html',
                         total_submissions=total_submissions,
                         pending_count=pending_count,
                         replied_count=replied_count,
                         total_blogs=total_blogs,
                         admin_username=session.get('admin_username'))

@app.route('/admin/contacts')
@login_required
def admin_contacts():
    submissions = ContactSubmission.query.order_by(ContactSubmission.timestamp.desc()).all()
    submissions_list = [s.to_dict() for s in submissions]
    
    return render_template('admin_contacts.html', 
                         submissions=submissions_list,
                         admin_username=session.get('admin_username'))

@app.route('/admin/submission/<int:submission_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_submission(submission_id):
    submission = ContactSubmission.query.get(submission_id)
    
    if not submission:
        flash('Submission not found', 'error')
        return redirect(url_for('admin_contacts'))
    
    if request.method == 'POST':
        reply_message = request.form.get('reply_message')
        
        if reply_message:
            submission.admin_reply = reply_message
            submission.status = 'replied'
            submission.reply_timestamp = datetime.utcnow()
            db.session.commit()
            
            flash('Reply sent successfully!', 'success')
            return redirect(url_for('admin_contacts'))
        else:
            flash('Reply message cannot be empty', 'error')
    
    return render_template('admin_reply.html', submission=submission.to_dict())

@app.route('/admin/submission/<int:submission_id>/delete')
@login_required
def delete_submission(submission_id):
    submission = ContactSubmission.query.get(submission_id)
    if submission:
        db.session.delete(submission)
        db.session.commit()
        flash('Submission deleted successfully', 'success')
    return redirect(url_for('admin_contacts'))

@app.route('/admin/blogs')
@login_required
def admin_blogs():
    posts = BlogPost.query.order_by(BlogPost.date.desc()).all()
    return render_template('admin_blogs.html', 
                         posts=posts,
                         admin_username=session.get('admin_username'))

@app.route('/admin/blog/new', methods=['GET', 'POST'])
@login_required
def new_blog():
    if request.method == 'POST':
        new_post = BlogPost(
            title=request.form.get('title'),
            slug=request.form.get('title').lower().replace(' ', '-'),
            category=request.form.get('category'),
            author=request.form.get('author'),
            read_time=request.form.get('read_time'),
            featured=request.form.get('featured') == 'on',
            image=request.form.get('image'),
            excerpt=request.form.get('excerpt'),
            content=request.form.get('content')
        )
        db.session.add(new_post)
        db.session.commit()
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin_blogs'))
    
    return render_template('admin_blog_form.html', post=None)

@app.route('/admin/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_blog(post_id):
    post = BlogPost.query.get(post_id)
    if not post:
        flash('Blog post not found', 'error')
        return redirect(url_for('admin_blogs'))
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.slug = request.form.get('title').lower().replace(' ', '-')
        post.category = request.form.get('category')
        post.author = request.form.get('author')
        post.read_time = request.form.get('read_time')
        post.featured = request.form.get('featured') == 'on'
        post.image = request.form.get('image')
        post.excerpt = request.form.get('excerpt')
        post.content = request.form.get('content')
        
        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin_blogs'))
    
    return render_template('admin_blog_form.html', post=post)

@app.route('/admin/blog/<int:post_id>/delete')
@login_required
def delete_blog(post_id):
    post = BlogPost.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        flash('Blog post deleted successfully', 'success')
    return redirect(url_for('admin_blogs'))

# ============ ADMIN TESTIMONIALS ROUTES ============
@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    testimonials_list = Testimonial.query.order_by(Testimonial.date.desc()).all()
    stats = Statistic.query.order_by(Statistic.order).all()
    videos = VideoStory.query.order_by(VideoStory.order).all()
    
    # Parse JSON results
    for t in testimonials_list:
        if t.results:
            t.results = json.loads(t.results)
    
    return render_template('admin_testimonials.html',
                         testimonials=testimonials_list,
                         statistics=stats,
                         video_stories=videos,
                         admin_username=session.get('admin_username'))

# Statistics Management Routes
@app.route('/admin/statistic/new', methods=['GET', 'POST'])
@login_required
def new_statistic():
    if request.method == 'POST':
        new_stat = Statistic(
            value=request.form.get('value'),
            label=request.form.get('label'),
            icon=request.form.get('icon'),
            order=int(request.form.get('order', Statistic.query.count() + 1))
        )
        db.session.add(new_stat)
        db.session.commit()
        flash('Statistic added successfully!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin_statistic_form.html', statistic=None)

@app.route('/admin/statistic/<int:stat_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_statistic(stat_id):
    stat = Statistic.query.get(stat_id)
    if not stat:
        flash('Statistic not found', 'error')
        return redirect(url_for('admin_testimonials'))
    
    if request.method == 'POST':
        stat.value = request.form.get('value')
        stat.label = request.form.get('label')
        stat.icon = request.form.get('icon')
        stat.order = int(request.form.get('order'))
        
        db.session.commit()
        flash('Statistic updated successfully!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin_statistic_form.html', statistic=stat)

@app.route('/admin/statistic/<int:stat_id>/delete')
@login_required
def delete_statistic(stat_id):
    stat = Statistic.query.get(stat_id)
    if stat:
        db.session.delete(stat)
        db.session.commit()
        flash('Statistic deleted successfully', 'success')
    return redirect(url_for('admin_testimonials'))

# Testimonial Management Routes
@app.route('/admin/testimonial/new', methods=['GET', 'POST'])
@login_required
def new_testimonial():
    if request.method == 'POST':
        results_text = request.form.get('results', '')
        results_list = [r.strip() for r in results_text.split('\n') if r.strip()]
        
        new_test = Testimonial(
            name=request.form.get('name'),
            location=request.form.get('location'),
            image=request.form.get('image'),
            rating=int(request.form.get('rating', 5)),
            testimonial=request.form.get('testimonial'),
            results=json.dumps(results_list),
            featured=request.form.get('featured') == 'on'
        )
        db.session.add(new_test)
        db.session.commit()
        flash('Testimonial added successfully!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin_testimonial_form.html', testimonial=None)

@app.route('/admin/testimonial/<int:test_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_testimonial(test_id):
    test = Testimonial.query.get(test_id)
    if not test:
        flash('Testimonial not found', 'error')
        return redirect(url_for('admin_testimonials'))
    
    if request.method == 'POST':
        results_text = request.form.get('results', '')
        results_list = [r.strip() for r in results_text.split('\n') if r.strip()]
        
        test.name = request.form.get('name')
        test.location = request.form.get('location')
        test.image = request.form.get('image')
        test.rating = int(request.form.get('rating', 5))
        test.testimonial = request.form.get('testimonial')
        test.results = json.dumps(results_list)
        test.featured = request.form.get('featured') == 'on'
        
        db.session.commit()
        flash('Testimonial updated successfully!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    # Parse results for display
    if test.results:
        test.results = json.loads(test.results)
    
    return render_template('admin_testimonial_form.html', testimonial=test)

@app.route('/admin/testimonial/<int:test_id>/delete')
@login_required
def delete_testimonial(test_id):
    test = Testimonial.query.get(test_id)
    if test:
        db.session.delete(test)
        db.session.commit()
        flash('Testimonial deleted successfully', 'success')
    return redirect(url_for('admin_testimonials'))

# Video Story Management Routes
@app.route('/admin/video/new', methods=['GET', 'POST'])
@login_required
def new_video():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        video_id = youtube_url.split('v=')[-1].split('&')[0] if 'v=' in youtube_url else youtube_url.split('/')[-1]
        
        new_vid = VideoStory(
            title=request.form.get('title'),
            description=request.form.get('description'),
            youtube_url=youtube_url,
            thumbnail=f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            duration=request.form.get('duration'),
            views=request.form.get('views', '0'),
            featured=request.form.get('featured') == 'on',
            order=int(request.form.get('order', VideoStory.query.count() + 1))
        )
        db.session.add(new_vid)
        db.session.commit()
        flash('Video story added successfully!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin_video_form.html', video=None)

@app.route('/admin/video/<int:video_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    video = VideoStory.query.get(video_id)
    if not video:
        flash('Video not found', 'error')
        return redirect(url_for('admin_testimonials'))
    
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        vid_id = youtube_url.split('v=')[-1].split('&')[0] if 'v=' in youtube_url else youtube_url.split('/')[-1]
        
        video.title = request.form.get('title')
        video.description = request.form.get('description')
        video.youtube_url = youtube_url
        video.thumbnail = f'https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg'
        video.duration = request.form.get('duration')
        video.views = request.form.get('views')
        video.featured = request.form.get('featured') == 'on'
        video.order = int(request.form.get('order'))
        
        db.session.commit()
        flash('Video story updated successfully!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    return render_template('admin_video_form.html', video=video)

@app.route('/admin/video/<int:video_id>/delete')
@login_required
def delete_video(video_id):
    video = VideoStory.query.get(video_id)
    if video:
        db.session.delete(video)
        db.session.commit()
        flash('Video story deleted successfully', 'success')
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('admin_login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created 'templates' directory")
    
    # Initialize database only if tables don't exist
    initialize_database()
    print("Database initialized successfully!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)