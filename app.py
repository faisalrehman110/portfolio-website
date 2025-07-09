from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

JSONBIN_ID = os.environ.get("JSONBIN_ID")
JSONBIN_API_KEY = os.environ.get("JSONBIN_API_KEY")
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"

headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': JSONBIN_API_KEY
}

def get_reviews():
    response = requests.get(JSONBIN_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get('record', [])
    return []

def save_reviews(reviews):
    requests.put(JSONBIN_URL, headers=headers, json=reviews)

# Admin credentials
USERNAME = 'faisal'
PASSWORD = 'Faisal@ali12'

# Editable pages and blogs data path
PAGES_DIR = 'pages'
BLOGS_FILE = 'blogs_data.json'
REVIEWS_FILE = 'reviews_data.json'

# Upload folders
IMAGE_UPLOAD_FOLDER = 'static/uploads/blogs/images'
VIDEO_UPLOAD_FOLDER = 'static/uploads/blogs/videos'
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_UPLOAD_FOLDER, exist_ok=True)

# Allowed editable HTML pages
allowed_pages = {
    'index.html', 'about.html', 'education.html', 'experience.html',
    'internships.html', 'certifications.html', 'blogs.html',
    'contact.html', 'resume.html', 'reviews.html'
}

# ---------- Public Routes ----------

@app.route('/')
@app.route('/index')
def homepage():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/experience')
def experience():
    return render_template('experience.html')

@app.route('/internships')
def internships():
    return render_template('internships.html')

@app.route('/certifications')
def certifications():
    return render_template('certifications.html')

@app.route('/blogs')
def blogs():
    blogs_data = []
    if os.path.exists(BLOGS_FILE):
        with open(BLOGS_FILE, 'r', encoding='utf-8') as f:
            blogs_data = json.load(f)
    return render_template('blogs.html', blogs=blogs_data)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

@app.route('/reviews')
def reviews():
    reviews = sorted(get_reviews(), key=lambda x: x['timestamp'], reverse=True)
    return render_template('reviews.html', reviews=reviews)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    new_review = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'rating': int(request.form.get('rating')),
        'comment': request.form.get('comment'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    try:
        # Use helper function instead of repeating API call
        reviews = get_reviews()
        reviews.append(new_review)

        update_response = requests.put(JSONBIN_URL, headers=headers, json=reviews)
        if update_response.status_code != 200:
            print("Error saving review to JSONBin:", update_response.text)

    except Exception as e:
        print("Error submitting review:", str(e))

    return redirect(url_for('reviews'))

# ---------- Admin Login ----------

@app.route('/admin', methods=['GET'])
def admin_login_form():
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == USERNAME and password == PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login.html', error='Invalid credentials')

@app.route('/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login_form'))

    blogs = []
    if os.path.exists(BLOGS_FILE):
        with open(BLOGS_FILE, 'r', encoding='utf-8') as f:
            blogs = json.load(f)

    return render_template('admin_dashboard.html', pages=sorted(allowed_pages), blogs=blogs)

# ---------- Page Editor API ----------

@app.route('/api/get_page_content')
def get_page_content():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    page = request.args.get('page')
    if not page or page not in allowed_pages:
        return jsonify({'error': 'Invalid page'}), 400

    page_path = os.path.join(PAGES_DIR, page)
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': f"Error reading page: {str(e)}"}), 500

@app.route('/api/save_page_content', methods=['POST'])
def save_page_content():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    page = data.get('page')
    content = data.get('content')

    if not page or page not in allowed_pages:
        return jsonify({'error': 'Invalid page'}), 400
    if content is None:
        return jsonify({'error': 'No content provided'}), 400

    page_path = os.path.join(PAGES_DIR, page)
    try:
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f"Error saving page: {str(e)}"}), 500

# ---------- Blog Upload & Delete ----------

@app.route('/upload_blog', methods=['POST'])
def upload_blog():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login_form'))

    title = request.form.get('title')
    description = request.form.get('description')
    image_file = request.files.get('image')
    video_file = request.files.get('video')

    image_path = ''
    video_path = ''

    if image_file and image_file.filename:
        filename = secure_filename(datetime.now().strftime('%Y%m%d%H%M%S_') + image_file.filename)
        full_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
        image_file.save(full_path)
        image_path = f"uploads/blogs/images/{filename}".replace("\\", "/")

    if video_file and video_file.filename:
        filename = secure_filename(datetime.now().strftime('%Y%m%d%H%M%S_') + video_file.filename)
        full_path = os.path.join(VIDEO_UPLOAD_FOLDER, filename)
        video_file.save(full_path)
        video_path = f"uploads/blogs/videos/{filename}".replace("\\", "/")

    blogs = []
    if os.path.exists(BLOGS_FILE):
        with open(BLOGS_FILE, 'r', encoding='utf-8') as f:
            blogs = json.load(f)

    blogs.append({
        'id': datetime.now().strftime('%Y%m%d%H%M%S'),
        'title': title,
        'description': description,
        'image': image_path,
        'video': video_path,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

    with open(BLOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(blogs, f, indent=2)

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_blog/<blog_id>', methods=['POST'])
def delete_blog(blog_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login_form'))

    if os.path.exists(BLOGS_FILE):
        with open(BLOGS_FILE, 'r', encoding='utf-8') as f:
            blogs = json.load(f)

        blogs = [b for b in blogs if b.get('id') != blog_id]

        with open(BLOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(blogs, f, indent=2)

    return redirect(url_for('admin_dashboard'))

# ---------- Logout ----------

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('homepage'))

# ---------- Run ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
