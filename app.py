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

# Embedded form HTML
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
                    <textarea class="form-control" name="team_bio
