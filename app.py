from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import io

app = Flask(__name__)
app.secret_key = 'pitchforge_mvp_key'

# Init DB
def init_db():
    conn = sqlite3.connect('pitchforge.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pitches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  idea_summary TEXT NOT NULL,
                  target_audience TEXT,
                  funding_ask REAL,
                  timeline_months INTEGER,
                  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        idea_summary = request.form['idea_summary']
        target_audience = request.form.get('target_audience', '')
        funding_ask_str = request.form.get('funding_ask', '')
        timeline_months_str = request.form.get('timeline_months', '')
        
        # Basic validation
        if not email or not idea_summary:
            flash('Email and idea summary are required!')
            return redirect(url_for('index'))
        
        # Safe number coercion
        try:
            funding_ask = float(funding_ask_str) if funding_ask_str else 0.0
            timeline_months = int(timeline_months_str) if timeline_months_str else 0
        except ValueError:
            flash('Funding ask and timeline must be valid numbers (or leave blank for defaults)!')
            return redirect(url_for('index'))
        
        conn = sqlite3.connect('pitchforge.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pitches (email, idea_summary, target_audience, funding_ask, timeline_months)
                     VALUES (?, ?, ?, ?, ?)''',
                  (email, idea_summary, target_audience, funding_ask, timeline_months))
        pitch_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Build deck buffer
        buffer = build_pitch_deck_buffer(pitch_id, idea_summary, target_audience, funding_ask, timeline_months)
        
        # Stream download
        return send_file(buffer, as_attachment=True, download_name=f'PitchForge_Deck_{pitch_id}.pptx',
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    
    return render_template('form.html')

def build_pitch_deck_buffer(pitch_id, summary, audience, ask, timeline):
    prs = Presentation()
    
    # Slide 1: Title
    slide_layout = prs.slide_layouts[0]  # Title slide
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "PitchForge MVP Deck"
    subtitle = slide.placeholders[1]
    subtitle.text = f"ID: {pitch_id} | Generated: {datetime.now().strftime('%Y-%m-%d')}"
    
    # Slide 2: Idea
    slide_layout = prs.slide_layouts[1]  # Title + Content
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "The Big Idea"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = summary
    for p in tf.paragraphs:
        p.font.size = Pt(18)
    
    # Slide 3: Market
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Target Market"
    content = slide.placeholders[1]
    content.text = f"Audience: {audience}\n\nOpportunity: Scalable to VCs & founders in [your niche]."
    
    # Slide 4: Ask
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Funding Ask"
    content = slide.placeholders[1]
    content.text = f"${ask:,.2f} | Timeline: {timeline} months\n\nMilestones: MVP launch, user acquisition."
    
    # Slides 5-10: Placeholders (use blank layout safely)
    placeholder_topics = ['Traction', 'Team', 'Financials', 'Roadmap', 'Contact', 'Q&A']
    blank_layout = prs.slide_layouts[6]  # Blank
    for i, topic in enumerate(placeholder_topics, 5):
        slide = prs.slides.add_slide(blank_layout)
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = f"Slide {i}: [Add your {topic} here]"
        p.alignment = PP_ALIGN.CENTER
        p.font.color.rgb = RGBColor(0, 0, 255)  # Blue
        p.font.size = Pt(24)
    
    # Save to buffer
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

@app.route('/success')
def success():
    return '''
    <html>
        <head><title>PitchForge MVP</title></head>
        <body>
            <h1>Success! Your pitch is forged.</h1>
            <p>Deck downloaded—check your files. <a href="/">Submit another?</a></p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
