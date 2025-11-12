from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import io
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'pitchforge_mvp_key'  # Change this in prod!

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
        
        # Build & stream deck
        buffer = build_pitch_deck_buffer(pitch_id, idea_summary, target_audience, funding_ask, timeline_months)
        return send_file(buffer, as_attachment=True, download_name=f'PitchForge_Deck_{pitch_id}.pptx',
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    
    return render_template('form.html')

def build_pitch_deck_buffer(pitch_id, summary, audience, ask, timeline):
    prs = Presentation()
    
    # Slide 1: Title
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "PitchForge Investment Deck"
    subtitle = slide.placeholders[1]
    subtitle.text = f"ID: {pitch_id} | Generated: {datetime.now().strftime('%Y-%m-%d')}"
    
    # Slide 2: Idea Summary
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "The Business Idea"
    content = slide.placeholders[1]
    content.text = summary
    
    # Slide 3: Target Audience
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Target Market & Audience"
    content = slide.placeholders[1]
    content.text = f"Audience: {audience}\n\nScalable investment opportunity for growth-stage ideas."
    
    # Slide 4: Financial Overview (with chart)
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Financial Highlights"
    content = slide.placeholders[1]
    content.text = f"Funding Ask: ${ask:,.2f}\nTimeline: {timeline} months\n\nProjections ready for scaling."
    
    # Embed bar chart (funding vs. timeline)
    chart_buffer = io.BytesIO()
    plt.figure(figsize=(6, 4))
    categories = ['Funding Ask ($)', 'Timeline (Months)']
    values = [ask, timeline]
    plt.bar(categories, values, color=['blue', 'green'])
    plt.title('Investment Snapshot')
    plt.ylabel('Value')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(chart_buffer, format='png', bbox_inches='tight')
    chart_buffer.seek(0)
    plt.close()
    
    # Add chart to slide
    left = Inches(1)
    top = Inches(2)
    slide.shapes.add_picture(chart_buffer, left, top, width=Inches(5))
    
    # Slides 5-8: Placeholders
    topics = ['Traction & Milestones', 'Team & Execution', 'Risks & Mitigation', 'Call to Action']
    blank_layout = prs.slide_layouts[6]
    for i, topic in enumerate(topics, 5):
        slide = prs.slides.add_slide(blank_layout)
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = f"Slide {i}: {topic}"
        p.alignment = PP_ALIGN.CENTER
        p.font.color.rgb = RGBColor(0, 0, 255)
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
            <p>Deck downloaded—ready for investors. <a href="/">Submit another?</a></p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
