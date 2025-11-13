from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file
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
import numpy as np

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

# Form HTML template (embedded for simplicity)
FORM_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>PitchForge MVP - Forge Your Pitch</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .form-card { background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); padding: 30px; max-width: 800px; margin: 50px auto; }
        .btn-forge { background: linear-gradient(45deg, #007bff, #0056b3); border: none; font-weight: bold; }
        .financial-row { display: flex; gap: 15px; margin-bottom: 15px; }
        .financial-col { flex: 1; }
        .ai-toggle { margin: 15px 0; font-style: italic; color: #6c757d; }
        .mrr-group { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-card">
            <h1 class="text-center mb-4 text-primary">PitchForge MVP: Forge your business idea investment pitch</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="alert alert-warning alert-dismissible fade show" role="alert">
                        {{ messages[0] }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endif %}
            {% endwith %}
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3">
                    <label class="form-label fw-bold">Email</label>
                    <input type="email" class="form-control" name="email" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold">Idea Summary (keep it punchy!)</label>
                    <textarea class="form-control" name="idea_summary" rows="3" required placeholder="e.g., AI tool for e-comm personalization"></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold">Target Audience</label>
                    <input type="text" class="form-control" name="target_audience" placeholder="e.g., VCs in startups">
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold">Team Bio</label>
                    <textarea class="form-control" name="team_bio" rows="2" placeholder="e.g., Experienced founders in tech & finance"></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold">Financial Upload (Excel/CSV for auto-fill metrics)</label>
                    <input type="file" class="form-control" name="financial_file" accept=".xlsx,.csv">
                </div>
                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" id="saas_mode">
                    <label class="form-check-label" for="saas_mode">SaaS Model? (Shows MRR field)</label>
                </div>
                <div class="financial-row">
                    <div class="financial-col">
                        <label class="form-label">EBITDA (last 12m, $)</label>
                        <input type="number" class="form-control" name="ebitda" step="0.01">
                    </div>
                    <div class="financial-col">
                        <label class="form-label">YoY Growth Rate (%)</label>
                        <input type="number" class="form-control" name="yoy_growth" step="0.01">
                    </div>
                </div>
                <div class="financial-row">
                    <div class="financial-col">
                        <label class="form-label">LTV ($)</label>
                        <input type="number" class="form-control" name="ltv" step="0.01">
                    </div>
                    <div class="financial-col">
                        <label class="form-label">CAC ($)</label>
                        <input type="number" class="form-control" name="cac" step="0.01">
                    </div>
                </div>
                <div class="financial-row">
                    <div class="financial-col">
                        <label class="form-label">Burn Rate ($/month)</label>
                        <input type="number" class="form-control" name="burn_rate" step="0.01">
                    </div>
                    <div class="financial-col">
                        <label class="form-label">Gross Margin (%)</label>
                        <input type="number" class="form-control" name="gross_margin" step="0.01">
                    </div>
                </div>
                <div class="mrr-group financial-row">
                    <div class="financial-col">
                        <label class="form-label">MRR ($)</label>
                        <input type="number" class="form-control" name="mrr" step="0.01">
                    </div>
                    <div class="financial-col">
                        <label class="form-label">Churn Rate (%)</label>
                        <input type="number" class="form-control" name="churn_rate" step="0.01">
                    </div>
                </div>
                <div class="financial-row">
                    <div class="financial-col">
                        <label class="form-label">Funding Ask ($)</label>
                        <input type="number" class="form-control" name="funding_ask" step="0.01">
                    </div>
                    <div class="financial-col">
                        <label class="form-label">Timeline (months)</label>
                        <input type="number" class="form-control" name="timeline_months" min="1">
                    </div>
                </div>
                <div class="form-check ai-toggle">
                    <input class="form-check-input" type="checkbox" name="ai_polish" id="ai_polish">
                    <label class="form-check-label" for="ai_polish">AI Polish My Summary? (Enhances for investor appeal)</label>
                </div>
                <button type="submit" class="btn btn-primary btn-forge w-100 py-3 fs-5">Forge It! 🚀</button>
            </form>
            <p class="text-center mt-4 small text-muted">Investment-ready deck generated instantly—test your pitch today.</p>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('saas_mode').addEventListener('change', function() {
            document.querySelector('.mrr-group').style.display = this.checked ? 'flex' : 'none';
        });
    </script>
</body>
</html>
'''

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
        
        # Validation
        if not email or not idea_summary:
            flash('Email and idea summary are required!')
            return render_template_string(FORM_HTML)
        
        # Upload auto-fill
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
                    df_columns_lower = df.columns.str.lower()
                    ebitda_match = df_columns_lower[df_columns_lower.str.contains('ebitda', case=False, na=False)].index
                    if len(ebitda_match) > 0:
                        col_name = df.columns[ebitda_match[0]]
                        ebitda_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    yoy_match = df_columns_lower[df_columns_lower.str.contains('yoy growth', case=False, na=False)].index
                    if len(yoy_match) > 0:
                        col_name = df.columns[yoy_match[0]]
                        yoy_growth_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    ltv_match = df_columns_lower[df_columns_lower.str.contains('ltv', case=False, na=False)].index
                    if len(ltv_match) > 0:
                        col_name = df.columns[ltv_match[0]]
                        ltv_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    cac_match = df_columns_lower[df_columns_lower.str.contains('cac', case=False, na=False)].index
                    if len(cac_match) > 0:
                        col_name = df.columns[cac_match[0]]
                        cac_str
