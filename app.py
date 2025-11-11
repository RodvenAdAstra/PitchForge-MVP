import streamlit as st
import matplotlib
matplotlib.use('Agg')  # Safety for headless/Playground - prevents display errors
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd  # Powers the beefed CSV magic

def generate_financial_viz(financials):
    """Beefed: Bar for KPIs (+ optional DSCR) + line for revenue; return base64 embed."""
    # Dynamic KPI list (optional DSCR)
    kpi_metrics = ['CAPEX ($M)', 'NPV ($M)', 'EBITDA ($M)', 'IRR (%)']
    kpi_values = [financials.get('capex', 0), financials.get('npv', 0), financials.get('ebitda', 0), financials.get('irr', 0)]
    kpi_colors = ['#FF6B6B', '#4