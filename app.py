from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
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

# Init DB
def init_db():
    conn = sqlite3.connect('pitchforge.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pitches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  idea_summary TEXT NOT NULL,
                  target_audience TEXT,
                  team_bio TEXT,
                  ebitda REAL,
                  yoy_growth REAL,
                  ltv REAL,
                  cac REAL,
                  burn_rate REAL,
                  gross_margin REAL,
                  mrr REAL,
                  churn_rate REAL,
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
        ebitda_str = request.form.get('ebitda', '')
        yoy_growth_str = request.form.get('yoy_growth', '')
        ltv_str = request.form.get('ltv', '')
        cac_str = request.form.get('cac', '')
        burn_rate_str = request.form.get('burn_rate', '')
        gross_margin_str = request.form.get('gross_margin', '')
        mrr_str = request.form.get('mrr', '')
        churn_rate_str = request.form.get('churn_rate', '')
        funding_ask_str = request.form.get('funding_ask', '')
        timeline_months_str = request.form.get('timeline_months', '')
        ai_polish = request.form.get('ai_polish', 'off')
        
        # AI polish
        if ai_polish == 'on':
            idea_summary = polish_text(idea_summary, ltv, cac, yoy_growth, churn_rate)
        
        # Validation
        if not email or not idea_summary:
            flash('Email and idea summary are required!')
            return redirect(url_for('index'))
        
        # Upload auto-fill (case-insensitive column match)
        financial_file = None
        parsed_columns = []
        if 'financial_file' in request.files:
            file = request.files['financial_file']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                financial_file = filename
                try:
                    df = pd.read_excel(file_path) if filename.endswith('.xlsx') else pd.read_csv(file_path)
                    columns = [col.lower() for col in df.columns]
                    parsed_columns = [col.title() for col in columns if col.lower() in ['ebitda', 'yoy growth', 'ltv', 'cac', 'burn rate', 'gross margin', 'mrr', 'churn rate']]
                    if parsed_columns:
                        flash(f'Parsed columns: {", ".join(parsed_columns)}—auto-filled where matched.')
                    # Match & fill (case-insensitive)
                    if 'ebitda' in columns:
                        ebitda_str = str(df['EBITDA'].iloc[0]) if not pd.isna(df['EBITDA'].iloc[0]) else ebitda_str
                    if 'yoy growth' in columns:
                        yoy_growth_str = str(df['YoY Growth'].iloc[0]) if not pd.isna(df['YoY Growth'].iloc[0]) else yoy_growth_str
                    if 'ltv' in columns:
                        ltv_str = str(df['LTV'].iloc[0]) if not pd.isna(df['LTV'].iloc[0]) else ltv_str
                    if 'cac' in columns:
                        cac_str = str(df['CAC'].iloc[0]) if not pd.isna(df['CAC'].iloc[0]) else cac_str
                    if 'burn rate' in columns:
                        burn_rate_str = str(df['Burn Rate'].iloc[0]) if not pd.isna(df['Burn Rate'].iloc[0]) else burn_rate_str
                    if 'gross margin' in columns:
                        gross_margin_str = str(df['Gross Margin'].iloc[0]) if not pd.isna(df['Gross Margin'].iloc[0]) else gross_margin_str
                    if 'mrr' in columns:
                        mrr_str = str(df['MRR'].iloc[0]) if not pd.isna(df['MRR'].iloc[0]) else mrr_str
                    if 'churn rate' in columns:
                        churn_rate_str = str(df['Churn Rate'].iloc[0]) if not pd.isna(df['Churn Rate'].iloc[0]) else churn_rate_str
                except Exception as e:
                    flash(f'Upload error: {str(e)}—manual entry still works.')
        
        # Safe numbers
        try:
            ebitda = float(ebitda_str) if ebitda_str else 0.0
            yoy_growth = float(yoy_growth_str) if yoy_growth_str else 0.0
            ltv = float(ltv_str) if ltv_str else 0.0
            cac = float(cac_str) if cac_str else 0.0
            burn_rate = float(burn_rate_str) if burn_rate_str else 0.0
            gross_margin = float(gross_margin_str) if gross_margin_str else 0.0
            mrr = float(mrr_str) if mrr_str else 0.0
            churn_rate = float(churn_rate_str) if churn_rate_str else 0.0
            funding_ask = float(funding_ask_str) if funding_ask_str else 0.0
            timeline_months = int(timeline_months_str) if timeline_months_str else 0
        except ValueError:
            flash('Metrics must be valid numbers (or upload for auto-fill)!')
            return redirect(url_for('index'))
        
        conn = sqlite3.connect('pitchforge.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pitches (email, idea_summary, target_audience, team_bio, ebitda, yoy_growth, ltv, cac, burn_rate, gross_margin, mrr, churn_rate, funding_ask, timeline_months, financial_file)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (email, idea_summary, target_audience, team_bio, ebitda, yoy_growth, ltv, cac, burn_rate, gross_margin, mrr, churn_rate, funding_ask, timeline_months, financial_file))
        pitch_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Build & stream deck
        buffer = build_pitch_deck_buffer(pitch_id, idea_summary, target_audience, team_bio, ebitda, yoy_growth, ltv, cac, burn_rate, gross_margin, mrr, churn_rate, funding_ask, timeline_months)
        return send_file(buffer, as_attachment=True, download_name=f'PitchForge_Deck_{pitch_id}.pptx',
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    
    return render_template('form.html')

def polish_text(summary, ltv, cac, yoy_growth, churn_rate):
    ratio = ltv / cac if cac else 0
    return f"Investor-Ready Pitch: {summary}. With LTV:CAC ratio of {ratio:.1f}, {yoy_growth:.1f}% YoY growth, and {churn_rate:.1f}% churn, this delivers scalable ROI."

def build_pitch_deck_buffer(pitch_id, summary, audience, team_bio, ebitda, yoy_growth, ltv, cac, burn_rate, gross_margin, mrr, churn_rate, ask, timeline):
    prs = Presentation()
    
    # Slide 1: Title (blue header)
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "PitchForge Investment Deck"
    title.text_frame.paragraphs[0].font.size = Pt(44)
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
    title.text_frame.paragraphs[0].font.bold = True
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(1.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(0, 123, 255)
    bg.line.fill.background()
    subtitle = slide.placeholders[1]
    subtitle.text = f"ID: {pitch_id} | {datetime.now().strftime('%Y-%m-%d')}"
    subtitle.text_frame.paragraphs[0].font.size = Pt(18)
    
    # Slide 2: Idea
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "The Business Idea"
    title.text_frame.paragraphs[0].font.size = Pt(32)
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 123, 255)
    content = slide.placeholders[1]
    content.text = summary
    content.text_frame.paragraphs[0].font.size = Pt(20)
    
    # Slide 3: Market
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Target Market"
    title.text_frame.paragraphs[0].font.size = Pt(32)
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 123, 255)
    content = slide.placeholders[1]
    content.text = f"Audience: {audience}\n\nScalable opportunity in high-growth sector."
    content.text_frame.paragraphs[0].font.size = Pt(20)
    
    # Slide 4: Team
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Our Team"
    title.text_frame.paragraphs[0].font.size = Pt(32)
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 123, 255)
    content = slide.placeholders[1]
    content.text = team_bio or "Proven team with execution expertise."
    content.text_frame.paragraphs[0].font.size = Pt(20)
    
    # Slide 5: Investment Metrics Chart (dynamic: skip if all zero, add labels)
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Investment Metrics Dashboard"
    title.text_frame.paragraphs[0].font.size = Pt(32)
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 123, 255)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.5), Inches(10), Inches(5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(248, 249, 250)
    bg.line.fill.background()
    # Values for charts (scale $ to thousands for visual)
    ebitda_k = ebitda / 1000 if ebitda else 0
    burn_k = burn_rate / 1000 if burn_rate else 0
    ltv_k = ltv / 1000 if ltv else 0
    cac_k = cac / 1000 if cac else 0
    mrr_k = mrr / 1000 if mrr else 0
    # Bar chart: EBITDA, Gross Margin, Burn Rate (only if any > 0)
    if ebitda > 0 or gross_margin > 0 or burn_rate > 0:
        chart1_buffer = io.BytesIO()
        plt.figure(figsize=(6, 4))
        bars_metrics = ['EBITDA ($k)', 'Gross Margin (%)', 'Burn Rate ($k/mo)']
        bars_values = [ebitda_k, gross_margin, burn_k]
        colors = ['green', 'blue', 'red']
        bars = plt.bar(bars_metrics, bars_values, color=colors, alpha=0.7)
        plt.title('Profitability & Burn')
        plt.xticks(rotation=45)
        # Label values on bars
        for bar, val in zip(bars, bars_values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'${val:,.0f}' if 'k' in bars_metrics[bar.get_x()] else f'{val:.1f}%', ha='center', va='bottom')
        plt.tight_layout()
        plt.savefig(chart1_buffer, format='png', bbox_inches='tight')
        chart1_buffer.seek(0)
        plt.close()
        slide.shapes.add_picture(chart1_buffer, Inches(0.5), Inches(2), width=Inches(4))
    else:
        # Placeholder text
        placeholder = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(3))
        tf = placeholder.text_frame
        p = tf.paragraphs[0]
        p.text = "Enter metrics (e.g., EBITDA $100k, Gross Margin 75%) for dynamic charts."
        p.font.size = Pt(18)
        p.alignment = PP_ALIGN.CENTER
    
    # Line chart: YoY Growth, Churn (only if any > 0)
    if yoy_growth > 0 or churn_rate > 0:
        chart2_buffer = io.BytesIO()
        plt.figure(figsize=(6, 4))
        line_x = ['YoY Growth (%)', 'Churn Rate (%)']
        line_y = [yoy_growth, churn_rate]
        plt.plot(line_x, line_y, marker='o', color='purple', linewidth=2)
        plt.title('Growth & Retention Trends')
        plt.xticks(rotation=45)
        # Label points
        for i, (x, y) in enumerate(zip(line_x, line_y)):
            plt.text(i, y + 0.5, f'{y:.1f}%', ha='center', va='bottom')
        plt.tight_layout()
        plt.savefig(chart2_buffer, format='png', bbox_inches='tight')
        chart2_buffer.seek(0)
        plt.close()
        slide.shapes.add_picture(chart2_buffer, Inches(5), Inches(2), width=Inches(4))
    # Pie: LTV vs CAC (only if both > 0)
    if ltv > 0 and cac > 0:
        pie_buffer = io.BytesIO()
        plt.figure(figsize=(4, 4))
        sizes = [ltv, cac]
        labels = ['LTV', 'CAC']
        colors = ['green', 'orange']
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('LTV vs CAC Ratio')
        plt.tight_layout()
        plt.savefig(pie_buffer, format='png', bbox_inches='tight')
        pie_buffer.seek(0)
        plt.close()
        slide.shapes.add_picture(pie_buffer, Inches(5), Inches(4.5), width=Inches(3))
    # SaaS note
    if mrr > 0:
        saas_note = slide.shapes.add_textbox(Inches(1), Inches(5.5), Inches(8), Inches(0.5))
        sf = saas_note.text_frame
        sp = sf.paragraphs[0]
        sp.text = f"MRR: ${mrr_k:,.0f}k | Strong recurring revenue stream."
        sp.font.size = Pt(16)
        sp.font.color.rgb = RGBColor(0, 128, 0)
    
    # Slide 6: Ask
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "The Investment Ask"
    title.text_frame.paragraphs[0].font.size = Pt(32)
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 123, 255)
    content = slide.placeholders[1]
    content.text = f"${ask:,.0f} | Timeline: {timeline} months\n\nFuel for acceleration and milestones."
    content.text_frame.paragraphs[0].font.size = Pt(20)
    
    # Slides 7-12: Placeholders (themed with icons)
    topics = ['Roadmap', 'Traction', 'Risks & Mitigation', 'Exit Strategy', 'Contact', 'Q&A']
    blank_layout = prs.slide_layouts[6]
    for i, topic in enumerate(topics, 7):
        slide = prs.slides.add_slide(blank_layout)
        # Header BG
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(1))
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(0, 123, 255)
        bg.line.fill.background()
        # Title
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.2), Inches(8), Inches(1))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = topic
        p.font.size = Pt(32)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER
        # Icon (arrow for growth topics)
        if topic in ['Roadmap', 'Traction', 'Exit Strategy']:
            icon = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(0.5), Inches(2), Inches(1), Inches(0.5))
            icon.fill.solid()
            icon.fill.fore_color.rgb = RGBColor(255, 215, 0)  # Gold
        # Content placeholder
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(4))
        cf = content_box.text_frame
        cp = cf.paragraphs[0]
        cp.text = f"Details for {topic.lower()}: Bullet points, timelines, or data visualizations here."
        cp.font.size = Pt(18)
        cp.alignment = PP_ALIGN.LEFT
    
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
            <p>Deck downloaded—metrics charted for investor impact. <a href="/">Submit another?</a></p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
