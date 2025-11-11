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
        base_msg = f"CAPEX=${round(financials.get('capex',0),2)}M, NPV=${round(financials.get('npv',0),2)}M, EBITDA=${round(financials.get('ebitda',0),2)}M, IRR={round(financials.get('irr',0),2)}%"
        dscr_str = f", DSCR={round(financials.get('dscr',0),2)}x" if financials.get('dscr') else ""
        st.sidebar.success(f"📊 Auto-parsed: {base_msg}{dscr_str} | Revenues: {rev_summary}")
        return financials
    except Exception as e:
        st.sidebar.error(f"Parse hiccup: {e}. Falling back to manual. Tip: Cols 'Metric' & 'Value'; add DSCR for credit plays.")
        return {}

def generate_ai_text(slide_type, company_name, sector, user_prompt, financials):
    """Tease AI fill: Prompt-based text for placeholders. (Scale to LLM API.)"""
    # MVP Mock: Structured output (replace with API call: e.g., openai.ChatCompletion)
    if slide_type == "problem_solution":
        return f"- Problem: Retail chains in LATAM face skyrocketing energy costs and ESG pressures, with 70% unable to afford solar upfront.\n- Solution: {company_name}'s fintech leasing—pay-per-kWh model slashes barriers, delivering {round(financials.get('irr',48),2)}% IRR while greening ops.\n- Edge: Blockchain-tracked savings, scalable to 10k sites by Y3."
    elif slide_type == "product_tech":
        return f"Core offering: AI-driven solar leasing platform with IoT monitoring for real-time yield optimization. Integrates tokenization for fractional ownership, targeting {sector} underserved by traditional finance."
    elif slide_type == "revenue_projection":
        return f"Projections: Y1 ${round(financials.get('revenue_y1',5.2),2)}M from 50 pilots, ramping to ${round(financials.get('revenue_y3',12.1),2)}M by Y3 via 30% MoM growth. Model assumes 80% utilization, conservative on {sector} adoption."
    return "[Gen in progress—add your prompt!]"

def generate_pitch_deck(company_name, financials, market_opportunity, team_highlights, ask_amount, ai_fills):
    """Updated: Inject AI text into placeholders."""
    viz_md = generate_financial_viz(financials)
    
    # AI Injections
    problem_solution = ai_fills.get('problem_solution', "- Problem: [Brief description - edit me!]\n- Solution: {company_name}'s innovative approach in [sector]")
    product_tech = ai_fills.get('product_tech', "- Core offering: [Brief tech/product desc - edit me!]")
    revenue_proj = ai_fills.get('revenue_projection', "- Revenue Projection: [Insert projections - edit me!]")
    
    # Conditional metrics (rounded)
    key_metrics = f"- **Key Metrics**: NPV: ${round(financials.get('npv', 0),2)}M, EBITDA: ${round(financials.get('ebitda', 0),2)}M, IRR: {round(financials.get('irr', 0),2)}%"
    if financials.get('dscr') is not None and financials['dscr'] > 0:
        key_metrics += f", DSCR: {round(financials['dscr'],2)}x"
    
    deck = f"""
# {company_name} Investment Pitch Deck

## Slide 1: Executive Summary
- **Company**: {company_name}
- **Opportunity**: {market_opportunity}
- **Ask**: ${ask_amount}M for [insert use of funds]
{key_metrics}

## Slide 2: Problem & Solution
{problem_solution}

## Slide 3: Market Opportunity
{market_opportunity}

## Slide 4: Product/Technology
{product_tech}

## Slide 5: Traction & Financials
{revenue_proj}
- Financial Highlights:
{viz_md}

## Slide 6: Team
{team_highlights}

## Slide 7: The Ask & Use of Funds
- Seeking: ${ask_amount}M
- Use: 40% Product Dev, 30% Marketing, 20% Ops, 10% Reserves

## Slide 8: Contact
Reach out to discuss: [Your contact - edit me!]
    """
    return deck

def generate_ai_cover_image_prompt(company_name, sector, user_prompt):
    """Tease: Build full prompt for cover gen (scale to API like Flux)."""
    return f"Creative AI pitch deck cover: {user_prompt}, {company_name} in {sector}, professional visuals with charts/graphs overlay, vibrant yet sleek, high-res 16:9."

def mock_ai_cover_image(prompt):  # MVP Mock: Placeholder base64 (replace with API call)
    """Mock gen: Returns base64 PNG (prod: Call image API, e.g., flux.1)."""
    # Simple gradient placeholder with text (for demo; real: API response)
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.imshow([[0.2, 0.4], [0.6, 0.8]], cmap='Blues', extent=[0, 16, 0, 9], aspect='auto')
    ax.text(8, 4.5, f"AI Cover: {prompt[:30]}...\n(PitchForge Mock—API Coming!)", ha='center', va='center', fontsize=20, color='white', weight='bold')
    ax.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"![AI Cover](data:image/png;base64,{img_base64})"

# Streamlit App Structure
st.title("🚀 PitchForge MVP: AI Text + Images Full Fixed")
st.markdown("Upload CSV, AI text/images, gen full deck. Copy Markdown to PPT/Google Slides.")

# FIXED: All core inputs first (ensures vars defined before AI)
with st.sidebar.expander("Input Data", expanded=True):
    company_name = st.text_input("Company Name", value="Power Fintech S.A.")
    market_opportunity = st.text_area("Market Opportunity (1-2 sentences)", value="LATAM solar energy boom: $XXB market by 2030, underserved retail chains.")
    team_highlights = st.text_area("Team Highlights", value="Led by experts in fintech and renewables with 20+ years combined.")
    ask_amount = st.number_input("Ask Amount ($M)", value=5.0, min_value=0.1)
    sector = st.text_input("Sector (for AI)", value="fintech renewables")  # For AI prompts

# Beefed CSV Upload Tease
st.sidebar.markdown("*Pro Tip: CSV cols A='Metric' (e.g., DSCR, EBITDA, Revenue_Y1), B='Value'. Optional for credit-focused pitches.*")
uploaded_file = st.sidebar.file_uploader("Upload Financials (CSV)", type=['csv'])
financials = {}
if uploaded_file is not None:
    financials = parse_financials_from_file(uploaded_file)

# Financials Inputs (auto-filled if uploaded, else manual)
with st.sidebar.expander("Financials", expanded=True):
    # Core KPIs
    if financials.get('capex') is not None:
        capex = st.number_input("CAPEX ($M)", value=financials['capex'], min_value=0.0)
    else:
        capex = st.number_input("CAPEX ($M)", value=6.1, min_value=0.0)
    if financials.get('npv') is not None:
        npv = st.number_input("NPV ($M)", value=financials['npv'], min_value=0.0)
    else:
        npv = st.number_input("NPV ($M)", value=2.3, min_value=0.0)
    if financials.get('ebitda') is not None:
        ebitda = st.number_input("EBITDA ($M)", value=financials['ebitda'], min_value=0.0)
    else:
        ebitda = st.number_input("EBITDA ($M)", value=3.5, min_value=0.0)
    # Optional DSCR (for credit requests)
    if financials.get('dscr') is not None:
        dscr = st.number_input("DSCR (x)", value=financials['dscr'], min_value=0.0)
    else:
        dscr = st.number_input("DSCR (x) [Optional for Credit]", value=1.5, min_value=0.0)
    if financials.get('irr') is not None:
        irr = st.number_input("IRR (%)", value=financials['irr'], min_value=0.0)
    else:
        irr = st.number_input("IRR (%)", value=48.0, min_value=0.0)

# Revenue Projections
with st.sidebar.expander("Revenue Projections ($M)", expanded=True):
    rev_y1 = st.number_input("Revenue Y1", value=financials.get('revenue_y1', 5.2), min_value=0.0)
    rev_y2 = st.number_input("Revenue Y2", value=financials.get('revenue_y2', 8.7), min_value=0.0)
    rev_y3 = st.number_input("Revenue Y3", value=financials.get('revenue_y3', 12.1), min_value=0.0)

# Update dict (DSCR only if >0 to keep optional)
final_dscr = dscr if dscr > 0 else None
financials.update({'capex': capex, 'npv': npv, 'ebitda': ebitda, 'irr': irr, 'dscr': final_dscr, 'revenue_y1': rev_y1, 'revenue_y2': rev_y2, 'revenue_y3': rev_y3})

# AI Text Assist
with st.sidebar.expander("🤖 AI Text Assist", expanded=False):
    st.markdown("Drop a prompt to auto-fill 'edit me!' fields.")
    slide_type = st.selectbox("Pick Slide", ["problem_solution", "product_tech", "revenue_projection"], format_func=lambda x: x.replace("_", " ").title())
    user_prompt_text = st.text_input("Your Brief/Prompt (e.g., 'solar leasing model')", value="Explain business model")
    
    if st.button("Gen AI Text"):
        with st.spinner("AI crafting text..."):
            ai_text = generate_ai_text(slide_type, company_name, sector, user_prompt_text, financials)
            st.text_area("Generated Text", value=ai_text, height=100, key=f"ai_text_{slide_type}")
            if 'ai_fills' not in st.session_state:
                st.session_state.ai_fills = {}
            st.session_state.ai_fills[slide_type] = ai_text
            st.success("Text ready! Gen deck to inject.")

# AI Cover Image Gen
with st.sidebar.expander("🖼️ AI Cover Image Gen", expanded=False):
    st.markdown("Prompt for Slide 1 hero image (auto-suggests from sector).")
    user_prompt_image = st.text_input("Cover Prompt (e.g., 'solar skyline with charts')", value=f"sleek {sector} visuals over LATAM skyline, blue-green palette")
    full_prompt = generate_ai_cover_image_prompt(company_name, sector, user_prompt_image)
    st.info(f"Full Prompt: {full_prompt}")
    
    if st.button("Gen AI Cover"):
        with st.spinner("AI rendering cover..."):
            cover_md = mock_ai_cover_image(full_prompt)  # Prod: Replace with API gen
            st.markdown(cover_md)
            if 'cover_image' not in st.session_state:
                st.session_state.cover_image = ""
            st.session_state.cover_image = cover_md
            st.success("Cover ready! Gen deck to embed in Slide 1.")

# Gen Button (pull text + image from session)
if st.button("Generate Deck"):
    ai_fills = st.session_state.get('ai_fills', {})
    cover_md = st.session_state.get('cover_image', "")
    with st.spinner("Crafting your full AI pitch..."):
        deck = generate_pitch_deck(company_name, financials, market_opportunity, team_highlights, ask_amount, ai_fills)
        # Inject cover into Slide 1
        if cover_md:
            deck = deck.replace("## Slide 1: Executive Summary", f"{cover_md}\n\n## Slide 1: Executive Summary")
        st.markdown(deck)
        st.download_button(
            label="Download as Markdown (w/ Images)",
            data=deck,
            file_name=f"{company_name.replace(' ', '_')}_FullAIPitchDeck.md",
            mime="text/markdown"
        )
else:
    st.info("👈 AI text/images → gen deck magic.")

# Footer
st.markdown("---")
st.markdown("*Full Fixed: All fns defined upfront—no NameErrors! Test cover gen w/ your solar prompt. Next: Real API for images/text? Let's launch.*")