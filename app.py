from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import io
import zipfile

app = Flask(__name__)
app.secret_key = 'pitchforge_mvp_key'

# Init DB (same as before)
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
        funding_ask = request.form.get('funding_ask', 0)
        timeline_months = request.form.get('timeline_months', 0)
        
        # Basic validation
        if not email or not idea_summary:
            flash('Email and idea summary are required!')
            return redirect(url_for('index'))
        
        conn = sqlite3.connect('pitchforge.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pitches (email, idea_summary, target_audience, funding_ask, timeline_months)
                     VALUES (?, ?, ?, ?, ?)''',
                  (email, idea_summary, target_audience, float(funding_ask), int(timeline_months)))
        pitch_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Build & serve deck
        deck_path = build_pitch_deck(pitch_id, idea_summary, target_audience, funding_ask, timeline_months)
        return send_file(deck_path, as_attachment=True, download_name=f'PitchForge_Deck_{pitch_id}.pptx',
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    
    return render_template('form.html')

def build_pitch_deck(pitch_id, summary, audience, ask, timeline):
    prs = Presentation()
    
    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    title.text = "PitchForge MVP Deck"
    subtitle = slide.placeholders[1]
    subtitle.text = f"ID: {pitch_id} | Generated: {datetime.now().strftime('%Y-%m-%d')}"
    
    # Slide 2: Problem/Solution (from summary)
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "The Big Idea"
    content = slide.placeholders[1]
    content.text = summary
    content.text_frame.paragraphs[0].font.size = Pt(18)
    
    # Slide 3: Market (audience)
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Target Market"
    content = slide.placeholders[1]
    content.text = f"Audience: {audience}\n\nOpportunity: Scalable to VCs & founders in [your niche]."
    
    # Slide 4: The Ask
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Funding Ask"
    content = slide.placeholders[1]
    content.text = f"${ask:,} | Timeline: {timeline} months\n\nMilestones: MVP launch, user acquisition."
    
    # Add more slides as needed (e.g., Traction, Team—hardcode placeholders for now)
    for i in range(5, 11):  # Slides 5-10: Boilerplate
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
        title = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
        tf = title.text_frame
        p = tf.paragraphs[0]
        p.text = f"Slide {i}: [Add your {['Traction', 'Team', 'Financials', 'Roadmap', 'Contact', 'Q&A'][i-5]} here]"
        p.alignment = PP_ALIGN.CENTER
        p.font.color.rgb = RGBColor(0, 0, 255)
    
    # Save to in-memory buffer
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    
    # Temp file path for send_file
    with open(f'/tmp/deck_{pitch_id}.pptx', 'wb') as f:
        f.write(buffer.getvalue())
    return f'/tmp/deck_{pitch_id}.pptx'

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
