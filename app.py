import os
import json
import re
import shutil
import time
import signal
import datetime
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

@app.route("/stories/<path:subpath>")
def serve_stories(subpath):
    # Serve story images for the preview
    return send_from_directory(os.path.join(WEBSITE_ROOT, 'stories'), subpath)

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
        
    if file:
        filename = secure_filename(file.filename)
        dest_folder = os.path.join(WEBSITE_ROOT, 'stories', 'images')
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        file_path = os.path.join(dest_folder, filename)
        file.save(file_path)
        return jsonify({"success": True, "path": f"stories/images/{filename}"})

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
            
    # Calculate stats dynamically
    short_stories = sum(1 for s in stories if s.get('type', 'Short Story') == 'Short Story')
    blogs = sum(1 for s in stories if s.get('type') == 'Blog')
    
    stats = {
        "Total": len(stories),
        "Short Stories": short_stories,
        "Blogs": blogs
    }
            
    return render_template("index.html", stories=stories, stats=stats)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    title = data.get('title', 'Untitled')
    description = data.get('description', '')
    canonical_url = data.get('canonical_url', '')
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
        
    # Strip all inline styles pasted from Word/Quill to ensure it perfectly inherits the main site's CSS (fonts, colors, dark mode)
    body = re.sub(r'\s*style="[^"]*"', '', body, flags=re.IGNORECASE)

    # Embed Videos & Add Sources
    content_html = embed_videos(body)
    
    # AdSense HTML to inject
    ad_html = """
    <div class="article-ad-container" style="margin: 0.5rem auto; text-align: center; display: flex; justify-content: center; width: 100%;">
        <ins class="adsbygoogle"
             style="display:inline-block; width:300px; height:250px;"
             data-ad-client="ca-pub-1416149954400854"
             data-ad-slot="auto"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
    </div>
    """
    
    # Inject Ads
    # 1. At the top
    content_html = ad_html + content_html
    
    # 2. After asterisks or native dividers
    def inject_ad_after_asterisks(match):
        tag = match.group(0)
        if tag.strip().lower().startswith('<hr'):
            return tag + '\n' + ad_html
            
        # Strip HTML tags to check the text content
        text_content = re.sub(r'<[^>]+>', '', tag).replace('&nbsp;', ' ').strip()
        non_space = re.sub(r'\s+', '', text_content)
        
        # Match if the text is purely dots, asterisks, or ellipsis (at least 2)
        if re.fullmatch(r'[\*\.…\s]+', text_content) and len(non_space) >= 2:
            return tag + '\n' + ad_html
        return tag

    content_html = re.sub(r'<p[^>]*>.*?</p>|<hr[^>]*>|<h[1-6][^>]*>.*?</h[1-6]>|<figure[^>]*>.*?</figure>', inject_ad_after_asterisks, content_html, flags=re.IGNORECASE|re.DOTALL)
    
    # 3. At the bottom
    content_html = content_html + ad_html
    
    if sources.strip():
        source_links = sources.split('\n')
        source_html = '<div class="sources-block" style="margin-top: 1rem; padding-top: 2rem; border-top: 1px solid #ddd;">'
        source_html += '<h3>Sources</h3><ul>'
        for link in source_links:
            if link.strip():
                source_html += f'<li><a href="{link.strip()}" target="_blank">{link.strip()}</a></li>'
        source_html += '</ul></div>'
        content_html += source_html
        
    # Build Summary block conditional on Content Type
    if image.endswith('-desktop.webp'):
        mobile_img = image.replace('-desktop.webp', '-mobile.webp')
        img_html = f'''
            <picture>
                <source media="(max-width: 600px)" srcset="../{mobile_img}">
                <img src="../{image}" alt="Featured image for {title}">
            </picture>'''
    else:
        img_html = f'<img src="../{image}" alt="Featured image for {title}">'
        
    summary_block = f'''
    <div class="reader-summary-block no-summary">
        <div class="summary-image">{img_html}
        </div>
    </div>
    '''
        
    # Replace Template Tokens
    final_html = template.replace('{{TITLE}}', title)
    final_html = final_html.replace('{{SUBHEADING}}', description)
    
    # Description logic: If empty, fallback to summary.
    meta_desc = description if description else summary
    final_html = final_html.replace('{{DESCRIPTION}}', meta_desc)
    
    # Canonical URL logic
    if canonical_url:
        canonical_tag = f'<link rel="canonical" href="{canonical_url}">'
        final_html = final_html.replace('{{CANONICAL_URL}}', canonical_tag)
    else:
        canonical_tag = f'<link rel="canonical" href="https://darsanhalan.com/stories/{filename}">'
        final_html = final_html.replace('{{CANONICAL_URL}}', canonical_tag)
        
    final_html = final_html.replace('{{SUMMARY_BLOCK}}', summary_block)
    final_html = final_html.replace('{{CONTENT}}', content_html)
    
    # Related Posts logic
    related_posts_html = ""
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                all_stories = json.load(f)
            
            # Mix both formats randomly
            current_id = filename.replace('.html', '')
            other_stories = [s for s in all_stories if s.get('id') != current_id]
            import random
            recent_stories = random.sample(other_stories, min(3, len(other_stories)))
            
            for s in recent_stories:
                img_url = s.get('image', 'assets/images/story_placeholder.jpg')
                if img_url.endswith('-desktop.webp'):
                    img_url = img_url.replace('-desktop.webp', '-mobile.webp')
                # Prefix with ../ because stories are rendered in /stories/ directory
                final_img_url = '../' + img_url.lstrip('/')
                title_ = s.get('title', '')
                author_ = "Coffee Highs" if s.get('type') == "Blog" else "Short Story"
                
                related_posts_html += f'''
                <div class="related-card">
                    <a href="{s['id']}.html">
                        <img src="{final_img_url}" alt="{title_}">
                        <span class="related-card-title" style="margin-top: 0.5rem; display: block;">{title_}</span>
                        <span class="related-card-author">{author_}</span>
                    </a>
                </div>
                '''
        except Exception as e:
            print(f"Error loading related posts: {e}")
            
    final_html = final_html.replace('{{RELATED_POSTS}}', related_posts_html)
    
    # Schema Generation
    current_date = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    full_image_url = f"https://darsanhalan.com/{image.lstrip('/')}"
    if type_ == "Blog":
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "description": meta_desc,
            "image": [full_image_url],
            "datePublished": current_date,
            "dateModified": current_date,
            "author": {
                "@type": "Person",
                "name": "Darsan Halan"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Darsan Halan",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://darsanhalan.com/assets/images/Darsan%20Logo.png"
                }
            }
        }
    else:
        schema = {
            "@context": "https://schema.org",
            "@type": "ShortStory",
            "name": title,
            "author": {
                "@type": "Person",
                "name": "Darsan Halan"
            },
            "abstract": meta_desc,
            "image": full_image_url,
            "datePublished": current_date,
            "genre": "Fiction"
        }
    
    schema_script = f'<script type="application/ld+json">\n{json.dumps(schema, indent=4)}\n</script>'
    final_html = final_html.replace('{{SCHEMA_MARKUP}}', schema_script)
    
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
    current_date_iso = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    metadata = {
        'id': filename.replace('.html', ''),
        'title': title,
        'type': type_,
        'summary': summary if summary else description,
        'image': image,
        'datePublished': current_date_iso
    }
        
    return jsonify({"success": True, "filename": filename, "preview_url": f"/preview/{filename}", "metadata": metadata})

@app.route("/preview/<filename>")
def preview(filename):
    return send_from_directory(TEMP_DIR, filename)

def rebuild_static_feeds(stories):
    # Sort stories by date descending
    # Fallback to current date for older stories without datePublished
    now_iso = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    for s in stories:
        if not s.get('datePublished'):
            s['datePublished'] = now_iso
            
    sorted_stories = sorted(stories, key=lambda x: x.get('datePublished', now_iso), reverse=True)
    
    blogs = [s for s in sorted_stories if s.get('type') == 'Blog']
    short_stories = [s for s in sorted_stories if s.get('type') == 'Short Story']
    
    # --- 1. index.html Carousel ---
    carousel_html = ""
    dots_html = ""
    for i, s in enumerate(blogs[:8]):
        date_obj = datetime.datetime.fromisoformat(s['datePublished'])
        date_str = date_obj.strftime("%b %d, %Y")
        img_url = s.get('image', 'assets/images/story_placeholder.jpg')
        desc = s.get('summary', '')
        if len(desc) > 100: desc = desc[:100] + '...'
        
        carousel_html += f"""
                        <li class="story-slide">
                            <article class="story-card" style="height: 100%; display: flex; flex-direction: column;">
                                <a href="stories/{s['id']}.html" style="flex-grow: 1; display: flex; flex-direction: column; text-decoration: none; color: inherit;">
                                    <div class="story-img" style="background-image: url('{img_url}'); height: 200px; background-size: cover; background-position: center;"></div>
                                    <div style="padding: 1.5rem; flex-grow: 1; display: flex; flex-direction: column;">
                                        <div class="story-meta" style="color: #888; font-size: 0.8rem; margin-bottom: 0.5rem;">Coffee Highs &bull; {date_str}</div>
                                        <h3 class="story-subheading" style="margin-bottom: 0.8rem;">{s['title']}</h3>
                                        <p class="story-body" style="flex-grow: 1;">{desc}</p>
                                        <span class="story-more-link" style="margin-top: 1rem; color: var(--color-midnight-blue); font-weight: 600;">Read more &rarr;</span>
                                    </div>
                                </a>
                            </article>
                        </li>"""
        active_class = " active" if i == 0 else ""
        dots_html += f'\n                    <button class="stories-dot{active_class}" aria-label="Go to slide {i + 1}"></button>'
        
    index_path = os.path.join(WEBSITE_ROOT, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            idx_content = f.read()
            
        idx_content = re.sub(
            r'<!-- CMS_COFFEE_HIGHS_CAROUSEL_START -->.*?<!-- CMS_COFFEE_HIGHS_CAROUSEL_END -->',
            f'<!-- CMS_COFFEE_HIGHS_CAROUSEL_START -->{carousel_html}\n                        <!-- CMS_COFFEE_HIGHS_CAROUSEL_END -->',
            idx_content, flags=re.DOTALL
        )
        idx_content = re.sub(
            r'<!-- CMS_COFFEE_HIGHS_DOTS_START -->.*?<!-- CMS_COFFEE_HIGHS_DOTS_END -->',
            f'<!-- CMS_COFFEE_HIGHS_DOTS_START -->{dots_html}\n                    <!-- CMS_COFFEE_HIGHS_DOTS_END -->',
            idx_content, flags=re.DOTALL
        )
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(idx_content)

    # --- 2. stories.html Grids ---
    def build_grid(items, type_label):
        html = ""
        for s in items:
            date_obj = datetime.datetime.fromisoformat(s['datePublished'])
            date_str = date_obj.strftime("%b %d, %Y")
            img_url = s.get('image', 'assets/images/story_placeholder.jpg')
            if img_url.endswith('-desktop.webp'):
                img_url = img_url.replace('-desktop.webp', '-mobile.webp')
            desc = s.get('summary', '')
            if len(desc) > 150: desc = desc[:150] + '...'
            
            html += f"""
                        <article class="story-card">
                            <a href="stories/{s['id']}.html">
                                <div class="story-img" style="background-image: url('{img_url}');"></div>
                                <div class="story-meta">{type_label} &bull; {date_str}</div>
                                <h3 class="story-subheading">{s['title']}</h3>
                                <p class="story-body">{desc}</p>
                                <span class="story-more-link">Read Story &rarr;</span>
                            </a>
                        </article>"""
        return html

    coffee_html = build_grid(blogs, "Coffee Highs")
    short_html = build_grid(short_stories, "Short Story")
    
    stories_path = os.path.join(WEBSITE_ROOT, "stories.html")
    if os.path.exists(stories_path):
        with open(stories_path, 'r', encoding='utf-8') as f:
            st_content = f.read()
            
        st_content = re.sub(
            r'<!-- CMS_COFFEE_HIGHS_FEED_START -->.*?<!-- CMS_COFFEE_HIGHS_FEED_END -->',
            f'<!-- CMS_COFFEE_HIGHS_FEED_START -->{coffee_html}\n                        <!-- CMS_COFFEE_HIGHS_FEED_END -->',
            st_content, flags=re.DOTALL
        )
        st_content = re.sub(
            r'<!-- CMS_SHORT_STORIES_FEED_START -->.*?<!-- CMS_SHORT_STORIES_FEED_END -->',
            f'<!-- CMS_SHORT_STORIES_FEED_START -->{short_html}\n                        <!-- CMS_SHORT_STORIES_FEED_END -->',
            st_content, flags=re.DOTALL
        )
        
        with open(stories_path, 'w', encoding='utf-8') as f:
            f.write(st_content)

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
        
    # Rebuild static HTML feeds across the site
    try:
        rebuild_static_feeds(stories)
    except Exception as e:
        print(f"Error rebuilding static feeds: {e}")
        
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
