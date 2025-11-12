from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import io
import pandas as pd
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'pitchforge_mvp_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Init DB (expanded for financials)
def init_db():
    conn = sqlite3.connect('pitchforge.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pitches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  idea_summary TEXT NOT NULL,
                  target_audience TEXT,
                  team_bio TEXT,
                  market_size REAL,
                  capex REAL,
                  npv REAL,
                  irr REAL,
                  funding_ask REAL,
                  timeline_months INTEGER,
                  financial_file TEXT,
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
        team_bio = request.form.get('team_bio', '')
        market_size_str = request.form.get('market_size', '')
        capex_str = request.form.get('capex', '')
        npv_str = request.form.get('npv', '')
        irr_str = request.form.get('irr', '')
        funding_ask_str = request.form.get('funding_ask', '')
        timeline_months_str = request.form.get('timeline_months', '')
        ai_polish = request.form.get('ai_polish', 'off')
        
        # AI text polish stub
        if ai_polish == 'on':
            idea_summary = polish_text(idea_summary)
        
        # Basic validation
        if not email or not idea_summary:
            flash('Email and idea summary are required!')
            return redirect(url_for('index'))
        
        # Upload & auto-fill
        financial_file = None
        if 'financial_file' in request.files:
            file = request.files['financial_file']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                financial_file = filename
                try:
                    df = pd.read_excel(file_path) if filename.endswith('.xlsx') else pd.read_csv(file_path)
                    market_size_str = str(df.get('Market Size', [0])[0]) if not pd.isna(df.get('Market Size', [0])[0]) else market_size_str
                    capex_str = str(df.get('CAPEX', [0])[0]) if not pd.isna(df.get('CAPEX', [0])[0]) else capex_str
                    npv_str = str(df.get('NPV', [0])[0]) if not pd.isna(df.get('NPV', [0])[0]) else npv_str
                    irr_str = str(df.get('IRR', [0])[0]) if not pd.isna(df.get('IRR', [0])[0]) else irr_str
                except Exception as e:
                    flash(f'Upload parsed partially: {str(e)}')
        
        # Safe numbers
        try:
            market_size = float(market_size_str) if market_size_str else 0.0
            capex = float(capex_str) if capex_str else 0.0
            npv = float(npv_str) if npv_str else 0.0
            irr = float(irr_str) if irr_str else 0.0
            funding_ask = float(funding_ask_str) if funding_ask_str else 0.0
            timeline_months = int(timeline_months_str) if timeline_months_str else 0
        except ValueError:
            flash('Financial fields must be valid numbers (or upload for auto-fill)!')
            return redirect(url_for('index'))
        
        conn = sqlite3.connect('pitchforge.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pitches (email, idea_summary, target_audience, team_bio, market_size, capex, npv, irr, funding_ask, timeline_months, financial_file)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (email, idea_summary, target_audience, team_bio, market_size, capex, npv, irr, funding_ask, timeline_months, financial_file))
        pitch_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Build & stream deck
        buffer = build_pitch_deck_buffer(pitch_id, idea_summary, target_audience, team_bio, market_size, capex, npv, irr, funding_ask, timeline_months)
        return send_file(buffer, as_attachment=True, download_name=f'PitchForge_Deck_{pitch_id}.pptx',
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    
    return render_template('form.html')

def polish_text(summary):
    # AI stub (expand for real API)
    return f"Polished Pitch: {summary}. This scalable business idea drives innovation and high ROI for investors."

def build_pitch_deck_buffer(pitch_id, summary, audience, team_bio, market_size, capex, npv, irr, ask, timeline):
    prs = Presentation()
    
    # Slide 1: Title
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "PitchForge Investment Deck"
    subtitle = slide.placeholders[1]
    subtitle.text = f"ID: {pitch_id} | {datetime.now().strftime('%Y-%m-%d')}"
    
    # Slide 2: Idea
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "The Business Idea"
    content = slide.placeholders[1]
    content.text = summary
    
    # Slide 3: Market
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Target Market"
    content = slide.placeholders[1]
    content.text = f"Audience: {audience}\nMarket Size: ${market_size:,.0f}M"
    
    # Slide 4: Team
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Our Team"
    content = slide.placeholders[1]
    content.text = team_bio or "Experienced founders ready to execute."
    
    # Slide 5: Financials with chart
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Financial Highlights"
    content = slide.placeholders[1]
    content.text = f"CAPEX: ${capex:,.0f}M | NPV: ${npv:,.0f}M | IRR: {irr:.1f}%"
    # Chart
    chart_buffer = io.BytesIO()
    plt.figure(figsize=(6, 4))
    metrics = ['NPV ($M)', 'IRR (%)', 'Funding Ask ($)']
    values = [npv, irr, ask]
    plt.bar(metrics, values, color=['blue', 'green', 'orange'])
    plt.title('Key Financial Metrics')
    plt.savefig(chart_buffer, format='png', bbox_inches='tight')
    chart_buffer.seek(0)
    plt.close()
    left = Inches(1)
    top = Inches(2)
    slide.shapes.add_picture(chart_buffer, left, top, width=Inches(5))
    
    # Slide 6: Ask
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "The Investment Ask"
    content = slide.placeholders[1]
    content.text = f"${ask:,.0f} | Timeline: {timeline} months\nMilestones: Launch and scale."
    
    # Slides 7-12: Placeholders
    topics = ['Roadmap', 'Traction', 'Risks', 'Exit Strategy', 'Contact', 'Q&A']
    blank_layout = prs.slide_layouts[6]
    for i, topic in enumerate(topics, 7):
        slide = prs.slides.add_slide(blank_layout)
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = f"Slide {i}: {topic}"
        p.alignment = PP_ALIGN.CENTER
        p.font.color.rgb = RGBColor(0, 0, 255)
        p.font.size = Pt(24)
    
    # Buffer save
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
