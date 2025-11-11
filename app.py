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
        ax2.plot(years, revenues, marker='o', linewidth=2.5, color='#FFD93D', markersize=8)
        ax2.fill_between(years, revenues, alpha=0.3, color='#FFD93D')
        ax2.set_title('Revenue Projections ($M)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Revenue', fontsize=10)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Value labels on points (rounded)
        for i, (year, rev) in enumerate(zip(years, revenues)):
            rounded_rev = round(rev, 2)
            ax2.annotate(f'${rounded_rev}M', (year, rev), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No Revenue Data\n(Add Revenue_Y1-3 to CSV)', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Revenue Projections', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # Base64 encode
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"![Financial Viz](data:image/png;base64,{img_base64})"

def parse_financials_from_file(uploaded_file):
    """Beefed: Parse CSV for CAPEX/NPV/EBITDA/DSCR/IRR + Revenue_Y1-3. Cols: 'Metric', 'Value'."""
    try:
        df = pd.read_csv(uploaded_file)
        
        financials = {}
        for _, row in df.iterrows():
            metric = str(row.get('Metric', '')).strip().upper()
            value = float(row.get('Value', 0))
            if 'CAPEX' in metric:
                financials['capex'] = value
            elif 'NPV' in metric:
                financials['npv'] = value
            elif 'EBITDA' in metric:
                financials['ebitda'] = value
            elif 'DSCR' in metric:
                financials['dscr'] = value
            elif 'IRR' in metric:
                financials['irr'] = value
            elif 'REVENUE_Y1' in metric:
                financials['revenue_y1'] = value
            elif 'REVENUE_Y2' in metric:
                financials['revenue_y2'] = value
            elif 'REVENUE_Y3' in metric:
                financials['revenue_y3'] = value
        
        # Preview message (conditional DSCR, rounded)
        rev_summary = f"Y1:${round(financials.get('revenue_y1',0),2)}M | Y2:${round(financials.get('revenue_y2',0),2)}M | Y3:${round(financials.get('revenue_y3',0),2)}M"
        base_msg = f"CAPEX=${round(financials.get('capex',0),2)}M, NPV=${round(financials.get('npv',0),2)}M, EBITDA=${round(financials.get('ebitda',0),