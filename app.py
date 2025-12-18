from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from functools import wraps
import hashlib
from datetime import datetime
import uuid

app = Flask(__name__)
# Generate a secret key: python -c "import os; print(os.urandom(24).hex())"
app.secret_key = 'your_secret_key_here_change_this_in_production'

# Hashed credentials (SHA-256)
# Username: Shramicadmin, Password: Shramic123
ADMIN_CREDENTIALS = {
    'username': 'Shramicadmin',
    'password_hash': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'  # SHA-256 of 'Shramic123'
}

# Store contact form submissions in memory (will reset on server restart)
contact_submissions = []

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to protect admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/testimonial')
def testimonial():
    return render_template('testimonial.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Generate unique tracking ID
        tracking_id = str(uuid.uuid4())[:8].upper()
        
        # Get form data
        submission = {
            'id': len(contact_submissions) + 1,
            'tracking_id': tracking_id,
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'subject': request.form.get('subject'),
            'message': request.form.get('message'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending',
            'admin_reply': None,
            'reply_timestamp': None
        }
        contact_submissions.append(submission)
        
        # Store tracking ID in session
        session['user_tracking_id'] = tracking_id
        session['user_name'] = submission['name']
        
        flash('Thank you for contacting us! Your tracking ID is: ' + tracking_id, 'success')
        return redirect(url_for('contact'))
    
    # Check if user has a tracking ID in session
    user_tracking_id = session.get('user_tracking_id')
    user_submission = None
    
    if user_tracking_id:
        # Find user's submission
        for sub in contact_submissions:
            if sub['tracking_id'] == user_tracking_id:
                user_submission = sub
                break
    
    return render_template('contact.html', user_submission=user_submission)

@app.route('/check-reply', methods=['POST'])
def check_reply():
    tracking_id = request.form.get('tracking_id', '').strip().upper()
    
    if not tracking_id:
        flash('Please enter your tracking ID', 'error')
        return redirect(url_for('contact'))
    
    # Find submission by tracking ID
    submission = None
    for sub in contact_submissions:
        if sub['tracking_id'] == tracking_id:
            submission = sub
            break
    
    if submission:
        # Store in session
        session['user_tracking_id'] = tracking_id
        session['user_name'] = submission['name']
        
        if submission['admin_reply']:
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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verify credentials
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
    # Get statistics
    total_submissions = len(contact_submissions)
    pending_count = sum(1 for s in contact_submissions if s['status'] == 'pending')
    replied_count = sum(1 for s in contact_submissions if s['status'] == 'replied')
    
    # Sort by most recent first
    sorted_submissions = sorted(contact_submissions, key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin_dashboard.html', 
                         submissions=sorted_submissions,
                         total_submissions=total_submissions,
                         pending_count=pending_count,
                         replied_count=replied_count,
                         admin_username=session.get('admin_username'))

@app.route('/admin/submission/<int:submission_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_submission(submission_id):
    submission = None
    for sub in contact_submissions:
        if sub['id'] == submission_id:
            submission = sub
            break
    
    if not submission:
        flash('Submission not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        reply_message = request.form.get('reply_message')
        
        if reply_message:
            submission['admin_reply'] = reply_message
            submission['status'] = 'replied'
            submission['reply_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            flash('Reply sent successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Reply message cannot be empty', 'error')
    
    return render_template('admin_reply.html', submission=submission)

@app.route('/admin/submission/<int:submission_id>/delete')
@login_required
def delete_submission(submission_id):
    global contact_submissions
    contact_submissions = [s for s in contact_submissions if s['id'] != submission_id]
    flash('Submission deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

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
    app.run(debug=True, host='0.0.0.0', port=5000)