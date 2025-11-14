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
            return render_template('form.html')
        
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
                    # Ebitda
                    ebitda_match = df_columns_lower[df_columns_lower.str.contains('ebitda', case=False, na=False)].index
                    if len(ebitda_match) > 0:
                        col_name = df.columns[ebitda_match[0]]
                        ebitda_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    # YoY Growth
                    yoy_match = df_columns_lower[df_columns_lower.str.contains('yoy growth', case=False, na=False)].index
                    if len(yoy_match) > 0:
                        col_name = df.columns[yoy_match[0]]
                        yoy_growth_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    # LTV
                    ltv_match = df_columns_lower[df_columns_lower.str.contains('ltv', case=False, na=False)].index
                    if len(ltv_match) > 0:
                        col_name = df.columns[ltv_match[0]]
                        ltv_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    # CAC
                    cac_match = df_columns_lower[df_columns_lower.str.contains('cac', case=False, na=False)].index
                    if len(cac_match) > 0:
                        col_name = df.columns[cac_match[0]]
                        cac_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    # Burn Rate
                    burn_match = df_columns_lower[df_columns_lower.str.contains('burn rate', case=False, na=False)].index
                    if len(burn_match) > 0:
                        col_name = df.columns[burn_match[0]]
                        burn_rate_str = pd.to_numeric(df[col_name].iloc[0], errors='coerce')
                        parsed_columns.append(col_name)
                    # Gross Margin
                    gross_match = df_columns_lower[df_columns_lower.str.contains('gross margin', case=False, na=False)].index
                    if len(gross_match) > 0:
                        col_name = df.columns[gross_match[0]]
                        gross_margin_str
