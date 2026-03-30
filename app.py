import os
import json
import re
import shutil
import time
import signal
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
import webbrowser

app = Flask(__name__)

# Constants - using relative paths for cross-platform GitHub compatibility
WEBSITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'darsan-halan-website'))
STORIES_DIR = os.path.join(WEBSITE_ROOT, "stories")
JSON_PATH = os.path.join(STORIES_DIR, "stories.json")
TEMPLATE_PATH = os.path.join(WEBSITE_ROOT, "reader_template.html")
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_builds")

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def generate_filename(title):
    # Convert title to a valid URL-friendly filename securely
    safe_title = secure_filename(title.lower().replace(' ', '-'))
    if not safe_title:
        safe_title = "untitled-story"
    return safe_title + '.html'

def embed_videos(html_content):
    # Support Quill's native video embed iframe class
    html_content = html_content.replace('class="ql-video"', 'class="ql-video" referrerpolicy="strict-origin-when-cross-origin" style="width: 100%; max-width: 560px; height: 315px; margin: 2rem auto; display: block;"')

    # YouTube Embed Regex for plain pasted URLs
    yt_regex = re.compile(r'<p>\s*(?:<a\s+[^>]*>)?\s*https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})[^<]*(?:</a>)?\s*</p>', re.IGNORECASE)
    html_content = yt_regex.sub(
        r'<div style="text-align: center; margin: 2rem 0;"><iframe width="100%" style="max-width:560px;" height="315" src="https://www.youtube.com/embed/\1" frameborder="0" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>', 
        html_content
    )
    
    # Facebook Embed Regex for plain pasted URLs
    fb_regex = re.compile(r'<p>\s*(?:<a\s+[^>]*>)?\s*(https?://(?:www\.)?facebook\.com/watch/\?v=\d+)[^<]*(?:</a>)?\s*</p>', re.IGNORECASE)
    html_content = fb_regex.sub(
        r'<div style="text-align: center; margin: 2rem 0;"><iframe src="https://www.facebook.com/plugins/video.php?href=\1&show_text=0&width=560" width="560" height="315" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowTransparency="true" allowFullScreen="true"></iframe></div>',
        html_content
    )
    
    return html_content

@app.route("/assets/<path:subpath>")
def serve_assets(subpath):
    # Serve CSS/JS/Images so the preview has a clean layout
    return send_from_directory(os.path.join(WEBSITE_ROOT, 'assets'), subpath)

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
        
    if file:
        filename = secure_filename(file.filename)
        dest_folder = os.path.join(WEBSITE_ROOT, 'assets', 'images')
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        file_path = os.path.join(dest_folder, filename)
        file.save(file_path)
        return jsonify({"success": True, "path": f"assets/images/{filename}"})

@app.route("/")
def index():
    # Fetch active stories for the side pane
    stories = []
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                stories = json.load(f)
        except Exception as e:
            print("Error loading stories.json:", e)
            
    # Calculate stats
    # For now, stories.json has {'id', 'title', 'summary', 'image'}
    # Categorization will depend on the real existing JSON, but we can default to Short Story
    stats = {
        "Total": len(stories),
        "Short Stories": len(stories),
        "Research": 0,
        "Articles": 0
    }
            
    return render_template("index.html", stories=stories, stats=stats)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    title = data.get('title', 'Untitled')
    subtitle = data.get('subtitle', '')
    summary = data.get('summary', '')
    type_ = data.get('type', 'Short Story')
    image = data.get('image', 'assets/images/story_placeholder.jpg')
    body = data.get('body', '')
    sources = data.get('sources', '')
    
    filename = generate_filename(title)
    
    if not image.strip():
        image = 'assets/images/story_placeholder.jpg'
        
    # Read Template
    if not os.path.exists(TEMPLATE_PATH):
        return jsonify({"success": False, "error": "reader_template.html not found in website root!"})
        
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
        
    # Embed Videos & Add Sources
    content_html = embed_videos(body)
    
    if sources.strip():
        source_links = sources.split('\n')
        source_html = '<div class="sources-block" style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #ddd;">'
        source_html += '<h3>Sources</h3><ul>'
        for link in source_links:
            if link.strip():
                source_html += f'<li><a href="{link.strip()}" target="_blank">{link.strip()}</a></li>'
        source_html += '</ul></div>'
        content_html += source_html
        
    # Build Summary block conditional on Content Type
    if type_ == "Short Story":
        summary_block = f'''
        <div class="reader-summary-block no-summary">
            <div class="summary-image">
                <img src="../{image}" alt="Featured image for {title}">
            </div>
        </div>
        '''
    else:
        summary_block = f'''
        <div class="reader-summary-block">
            <div class="summary-text">
                <h3>Summary</h3>
                <p>{summary}</p>
            </div>
            <div class="summary-image">
                <img src="../{image}" alt="Featured image for {title}">
            </div>
        </div>
        '''
        
    # Replace Template Tokens
    final_html = template.replace('{{TITLE}}', title)
    final_html = final_html.replace('{{SUBHEADING}}', subtitle)
    final_html = final_html.replace('{{SUMMARY_BLOCK}}', summary_block)
    final_html = final_html.replace('{{CONTENT}}', content_html)
    
    # Fix paths for nested folder execution
    final_html = final_html.replace('href="assets/', 'href="../assets/')
    final_html = final_html.replace('src="assets/', 'src="../assets/')
    final_html = final_html.replace('href="index.html', 'href="../index.html')
    final_html = final_html.replace('href="stories.html', 'href="../stories.html')
    final_html = final_html.replace('href="contact.html', 'href="../contact.html')
    final_html = final_html.replace('href="medium-reader.html', 'href="../medium-reader.html')
    
    # Save Temp File
    temp_path = os.path.join(TEMP_DIR, filename)
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    # Generate Metadata Payload for Approval later
    metadata = {
        'id': filename.replace('.html', ''),
        'title': title,
        'summary': summary if summary else subtitle,
        'image': image
    }
        
    return jsonify({"success": True, "filename": filename, "preview_url": f"/preview/{filename}", "metadata": metadata})

@app.route("/preview/<filename>")
def preview(filename):
    return send_from_directory(TEMP_DIR, filename)

@app.route("/approve", methods=["POST"])
def approve():
    data = request.json
    filename = data.get('filename')
    metadata = data.get('metadata')
    
    if not filename or not metadata:
        return jsonify({"success": False, "error": "Missing filename or metadata."})
        
    # Move file to live directory
    temp_path = os.path.join(TEMP_DIR, filename)
    live_path = os.path.join(STORIES_DIR, filename)
    
    if not os.path.exists(temp_path):
        return jsonify({"success": False, "error": "Draft file not found! Did you generate it?"})
        
    shutil.copyfile(temp_path, live_path)
    
    # Update stories.json
    stories = []
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                stories = json.load(f)
            except:
                pass
                
    # Remove existing entry if it exists to overwrite
    stories = [s for s in stories if s.get('id') != metadata['id']]
    
    # Prepend new story
    stories.insert(0, metadata)
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=4)
        
    return jsonify({"success": True})

@app.route("/shutdown", methods=["POST"])
def shutdown():
    print("Received shutdown signal from frontend. Closing local server...")
    os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({"success": True})

if __name__ == "__main__":
    url = "http://localhost:5000"
    print(f"Opening CMS in browser at: {url}")
    # Small delay to ensure server thread starts
    time.sleep(0.5)
    webbrowser.open(url)
    app.run(port=5000, debug=False)
