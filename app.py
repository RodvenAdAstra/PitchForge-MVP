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
    kpi_colors = ['#FF6B6B', '#4ECDC4', '#FFD93D', '#45B7D1']
    
    # Add DSCR if present (for credit requests)
    if financials.get('dscr') is not None and financials['dscr'] > 0:
        kpi_metrics.append('DSCR (x)')
        kpi_values.append(financials['dscr'])
        kpi_colors.append('#28A745')  # Green for coverage win
    
    # Bar chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    bars = ax1.bar(kpi_metrics, kpi_values, color=kpi_colors)
    ax1.set_title('Key Financials', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Value', fontsize=10)
    ax1.tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars, kpi_values):
        height = bar.get_height()
        # FIXED: Round floats to 2 decimals for clean labels
        rounded_val = round(val, 2) if isinstance(val, float) else val
        label = f'${rounded_val}M' if '$M' in kpi_metrics[kpi_values.index(val)] else f'{rounded_val}%' if '%' in kpi_metrics[kpi_values.index(val)] else f'{rounded_val}x'
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                 label, ha='center', va='bottom', fontsize=9)
    
    # Right: Revenue Line (if data exists)
    revenues = [financials.get(f'revenue_y{i}', 0) for i in range(1, 4)]
    if any(revenues):  # Only plot if revenue data
        years = ['Y1', 'Y2', 'Y3']
        ax2.plot(years