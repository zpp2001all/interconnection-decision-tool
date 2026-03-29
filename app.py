import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="Interconnection Decision Recommender",
    layout="wide"
)

# -----------------------------
# STYLING
# -----------------------------
st.markdown("""
<style>
    .main {
        background-color: #08111f;
    }
    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }
    h1, h2, h3 {
        letter-spacing: -0.02em;
    }
    .subtle {
        color: #9fb0c7;
        font-size: 0.95rem;
    }
    .section-card {
        background: linear-gradient(180deg, rgba(20,31,49,0.96) 0%, rgba(11,20,35,0.96) 100%);
        border: 1px solid rgba(130,150,180,0.18);
        border-radius: 16px;
        padding: 18px 18px 14px 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        margin-bottom: 14px;
    }
    .decision-box {
        border-radius: 16px;
        padding: 18px;
        border: 1px solid rgba(130,150,180,0.18);
        background: linear-gradient(180deg, rgba(20,31,49,0.96) 0%, rgba(11,20,35,0.96) 100%);
        min-height: 170px;
    }
    .decision-proceed {
        color: #34d399;
        font-weight: 700;
        font-size: 1.6rem;
    }
    .decision-hold {
        color: #fbbf24;
        font-weight: 700;
        font-size: 1.6rem;
    }
    .decision-withdraw {
        color: #f87171;
        font-weight: 700;
        font-size: 1.6rem;
    }
    .pill {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        background: rgba(72, 187, 255, 0.12);
        color: #b8e3ff;
        border: 1px solid rgba(72, 187, 255, 0.18);
        font-size: 0.82rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
    .footnote {
        color: #8ea0bb;
        font-size: 0.84rem;
    }
    .metric-card {
        background: linear-gradient(180deg, rgba(19,30,47,1) 0%, rgba(10,17,29,1) 100%);
        border: 1px solid rgba(130,150,180,0.16);
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 8px 22px rgba(0,0,0,0.16);
        min-height: 118px;
        margin-bottom: 10px;
    }
    .metric-label {
        color: #93a4bd;
        font-size: 0.92rem;
        margin-bottom: 0.45rem;
    }
    .metric-value {
        color: #f8fbff;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: clip;
    }
    .metric-value-sm {
        color: #f8fbff;
        font-size: 2.0rem;
        font-weight: 700;
        line-height: 1.1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: clip;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HELPERS
# -----------------------------
def fmt_dollar(x):
    return f"${x:,.0f}"

def clamp(value, low, high):
    return max(low, min(high, value))

def pct(x):
    return f"{x:.1%}"

def card(label, value, small=False):
    value_class = "metric-value-sm" if small else "metric-value"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="{value_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div class="section-card">
    <h1 style="margin-bottom:0.25rem;">⚡ Interconnection Decision Recommender</h1>
    <div class="subtle">
        Simplified decision-support dashboard for renewable project advancement at interconnection milestones.
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Scenario Toggles")

scenario = st.sidebar.selectbox(
    "Scenario",
    ["Base Case", "Bull Case", "Bear Case", "Fast Permit", "High NU Cost", "ITC Stress"]
)

project_type = st.sidebar.selectbox(
    "Project Type",
    ["Solar Only", "Solar + BESS", "BESS Only"]
)

st.sidebar.header("Valuation Basis")

valuation_basis = st.sidebar.selectbox(
    "Valuation Basis",
    ["Unlevered", "Levered-lite"]
)

debt_pct = 0.0
debt_rate = 0.0
tax_equity_proceeds = 0.0

if valuation_basis == "Levered-lite":
    debt_pct = st.sidebar.slider("Debt % of Base Capex", min_value=0.0, max_value=0.80, value=0.50, step=0.05)
    debt_rate = st.sidebar.slider("Debt Interest Rate", min_value=0.03, max_value=0.15, value=0.08, step=0.005)
    tax_equity_proceeds = st.sidebar.number_input(
        "Tax Equity Proceeds at COD ($)",
        min_value=0,
        max_value=500000000,
        value=30000000,
        step=1000000,
    )

st.sidebar.header("Project Configuration")

mw_dc = 0.0
mw_ac_inv = 0.0
mw_ac_poi = 0.0
bess_power_mw = 0.0

if project_type in ["Solar Only", "Solar + BESS"]:
    mw_dc = st.sidebar.number_input("Solar Array Size (MWdc)", min_value=50.0, max_value=500.0, value=150.0, step=5.0)
    mw_ac_inv = st.sidebar.number_input("Inverter Limit (MWac)", min_value=40.0, max_value=500.0, value=120.0, step=5.0)
    mw_ac_poi = st.sidebar.number_input("POI Limit (MWac Delivered)", min_value=40.0, max_value=500.0, value=110.0, step=5.0)

if project_type in ["Solar + BESS", "BESS Only"]:
    default_bess = 100.0 if project_type == "BESS Only" else 75.0
    bess_power_mw = st.sidebar.number_input("BESS Power Capacity (MW)", min_value=10.0, max_value=500.0, value=default_bess, step=5.0)

st.sidebar.header("Core Inputs")

if project_type == "BESS Only":
    capex_per_mw = st.sidebar.number_input("BESS Capex ($/MW)", min_value=500000, max_value=3000000, value=1000000, step=50000)
    opex_per_mw = st.sidebar.number_input("BESS Opex ($/MW/yr)", min_value=5000, max_value=60000, value=18000, step=1000)
else:
    capex_per_mw = st.sidebar.number_input("Solar Capex ($/MWdc)", min_value=800000, max_value=2500000, value=1200000, step=50000)
    opex_per_mw = st.sidebar.number_input("Solar Opex ($/MWdc/yr)", min_value=5000, max_value=50000, value=20000, step=1000)

nu_cost = st.sidebar.number_input("Network Upgrade Cost ($)", min_value=0, max_value=150000000, value=20000000, step=1000000)
deposit = st.sidebar.number_input("Next Decision Deposit ($)", min_value=0, max_value=20000000, value=1500000, step=100000)

permit_prob = st.sidebar.slider("Permit Probability", min_value=0.0, max_value=1.0, value=0.70, step=0.01)
timeline_years = st.sidebar.slider("Time to COD (yrs)", min_value=1, max_value=7, value=4)
discount_rate = st.sidebar.slider("Discount Rate", min_value=0.05, max_value=0.15, value=0.08, step=0.005)

st.sidebar.header("Life / Revenue Term")

contract_term_years = st.sidebar.slider("Contract Term (years)", min_value=1, max_value=25, value=10, step=1)
useful_life_years = st.sidebar.slider("Useful Life (years)", min_value=5, max_value=40, value=20, step=1)

if contract_term_years > useful_life_years:
    contract_term_years = useful_life_years
    st.sidebar.caption("Contract term cannot exceed useful life. Contract term was aligned to useful life.")

capacity_factor = 0.0
degradation_rate = 0.0

if project_type in ["Solar Only", "Solar + BESS"]:
    st.sidebar.header("Solar Operating Inputs")
    capacity_factor = st.sidebar.slider("Solar Capacity Factor", min_value=0.15, max_value=0.40, value=0.25, step=0.01)
    degradation_rate = st.sidebar.slider("Annual Solar Degradation", min_value=0.0, max_value=0.02, value=0.005, step=0.001)
    st.sidebar.caption(
        "Capacity factor converts delivered MW at POI into annual MWh production. Degradation reduces annual solar output over time."
    )

st.sidebar.header("Contracted Revenue")
contracted_energy_price = st.sidebar.number_input("Contracted Energy Price ($/MWh)", min_value=0, max_value=250, value=72, step=1)
contracted_capacity_price = st.sidebar.number_input("Contracted Capacity Revenue ($/MW-yr)", min_value=0, max_value=250000, value=85000, step=5000)

st.sidebar.header("Merchant Revenue / Curves")
base_price = st.sidebar.number_input("Merchant Energy Price ($/MWh)", min_value=20, max_value=250, value=70, step=1)
price_growth = st.sidebar.slider("Merchant Energy Growth %", min_value=0.00, max_value=0.06, value=0.02, step=0.005)
merchant_capacity_price = st.sidebar.number_input("Merchant Capacity Revenue ($/MW-yr)", min_value=0, max_value=250000, value=80000, step=5000)
basis = st.sidebar.number_input("Basis Discount ($/MWh)", min_value=-20, max_value=10, value=-5, step=1)

bess_margin = 0.0
if project_type in ["Solar + BESS", "BESS Only"]:
    st.sidebar.header("BESS Revenue")
    bess_margin = st.sidebar.number_input("BESS Revenue ($/MW-yr)", min_value=0, max_value=200000, value=40000, step=5000)
    st.sidebar.caption(
        "BESS revenue is simplified as annual gross value per MW of battery power capacity."
    )

st.sidebar.header("Tax Attribute / Safe Harbor")
base_itc_prob = st.sidebar.slider("ITC Capture Probability", min_value=0.0, max_value=1.0, value=0.85, step=0.01)

energy_community = st.sidebar.selectbox(
    "Energy Community Bonus Adder",
    ["No", "Possible", "Likely", "Secured"]
)

domestic_content = st.sidebar.selectbox(
    "Domestic Content Bonus Adder",
    ["No", "Possible", "Likely", "Secured"]
)

safe_harbor_status = st.sidebar.selectbox(
    "Safe Harbor Status",
    ["None", "Planned", "Secured"]
)

safe_harbor_method = st.sidebar.selectbox(
    "Safe Harbor Method",
    ["None", "5% Cost Safe Harbor", "Physical Work Test"]
)

safe_harbor_deadline_year = st.sidebar.number_input(
    "Safe Harbor Deadline Year",
    min_value=2024,
    max_value=2035,
    value=2028,
    step=1
)

schedule_buffer_days = st.sidebar.slider(
    "Schedule Buffer to Deadline (days)",
    min_value=0,
    max_value=180,
    value=60,
    step=5
)

# -----------------------------
# SCENARIO ADJUSTMENTS
# -----------------------------
scenario_notes = []

if scenario == "Bull Case":
    base_price += 10
    merchant_capacity_price += 15000
    contracted_energy_price += 5
    contracted_capacity_price += 10000
    permit_prob = clamp(permit_prob + 0.05, 0, 1)
    scenario_notes.append("Higher contracted and merchant pricing with improved overall outlook.")
elif scenario == "Bear Case":
    base_price -= 10
    merchant_capacity_price -= 15000
    contracted_energy_price -= 5
    contracted_capacity_price -= 10000
    permit_prob = clamp(permit_prob - 0.05, 0, 1)
    scenario_notes.append("Lower pricing and weaker permit outlook.")
elif scenario == "Fast Permit":
    timeline_years = max(1, timeline_years - 1)
    permit_prob = clamp(permit_prob + 0.10, 0, 1)
    scenario_notes.append("Accelerated local permitting assumption.")
elif scenario == "High NU Cost":
    nu_cost += 10000000
    scenario_notes.append("Higher network upgrade exposure.")
elif scenario == "ITC Stress":
    base_itc_prob = max(0.0, base_itc_prob - 0.20)
    scenario_notes.append("Reduced confidence in tax attribute capture.")

bonus_map = {
    "No": 0.00,
    "Possible": 0.30,
    "Likely": 0.70,
    "Secured": 1.00,
}

energy_community_prob = bonus_map[energy_community]
domestic_content_prob = bonus_map[domestic_content]

statutory_itc_if_achieved = 0.30 + (0.10 * energy_community_prob) + (0.10 * domestic_content_prob)
statutory_itc_if_achieved = clamp(statutory_itc_if_achieved, 0.0, 0.50)

safe_harbor_risk = 0.0
if safe_harbor_status == "None":
    safe_harbor_risk += 20
elif safe_harbor_status == "Planned":
    safe_harbor_risk += 10

if safe_harbor_method == "None":
    safe_harbor_risk += 10

if schedule_buffer_days < 60:
    safe_harbor_risk += 15
elif schedule_buffer_days < 90:
    safe_harbor_risk += 8

if timeline_years > 4:
    safe_harbor_risk += 10

safe_harbor_risk = clamp(safe_harbor_risk, 0, 100)

# -----------------------------
# CALCULATIONS
# -----------------------------
years = np.arange(1, useful_life_years + 1)

merchant_energy_prices = base_price * (1 + price_growth) ** (years - 1)
effective_merchant_prices = merchant_energy_prices + basis

annual_generation_series = np.zeros_like(years, dtype=float)
energy_revenue_contracted = np.zeros_like(years, dtype=float)
energy_revenue_merchant = np.zeros_like(years, dtype=float)

contract_mask = years <= contract_term_years
merchant_mask = years > contract_term_years

base_generation_mwh = 0.0
if project_type in ["Solar Only", "Solar + BESS"]:
    base_generation_mwh = mw_ac_poi * 8760 * capacity_factor
    annual_generation_series = np.array(
        [base_generation_mwh * ((1 - degradation_rate) ** (yr - 1)) for yr in years],
        dtype=float
    )

    energy_revenue_contracted = np.where(
        contract_mask,
        annual_generation_series * contracted_energy_price,
        0.0
    )

    energy_revenue_merchant = np.where(
        merchant_mask,
        annual_generation_series * effective_merchant_prices,
        0.0
    )

capacity_revenue_mw = 0.0
if project_type == "Solar Only":
    capacity_revenue_mw = mw_ac_poi
elif project_type == "Solar + BESS":
    capacity_revenue_mw = mw_ac_poi + bess_power_mw
elif project_type == "BESS Only":
    capacity_revenue_mw = bess_power_mw

contracted_capacity_revenue = np.where(
    contract_mask,
    capacity_revenue_mw * contracted_capacity_price,
    0.0
).astype(float)

merchant_capacity_revenue = np.where(
    merchant_mask,
    capacity_revenue_mw * merchant_capacity_price,
    0.0
).astype(float)

revenue_bess = np.zeros_like(years, dtype=float)
if project_type in ["Solar + BESS", "BESS Only"]:
    revenue_bess = np.full_like(years, bess_power_mw * bess_margin, dtype=float)

total_revenue = (
    energy_revenue_contracted
    + energy_revenue_merchant
    + contracted_capacity_revenue
    + merchant_capacity_revenue
    + revenue_bess
)

if project_type == "Solar Only":
    base_capex = mw_dc * capex_per_mw
    annual_opex = mw_dc * opex_per_mw
elif project_type == "Solar + BESS":
    solar_capex = mw_dc * capex_per_mw
    solar_opex = mw_dc * opex_per_mw
    bess_capex_proxy = bess_power_mw * 900000
    bess_opex_proxy = bess_power_mw * 15000
    base_capex = solar_capex + bess_capex_proxy
    annual_opex = solar_opex + bess_opex_proxy
else:
    base_capex = bess_power_mw * capex_per_mw
    annual_opex = bess_power_mw * opex_per_mw

total_capex = base_capex + nu_cost

debt_proceeds = 0.0
annual_debt_interest = 0.0
if valuation_basis == "Levered-lite":
    debt_proceeds = base_capex * debt_pct
    annual_debt_interest = debt_proceeds * debt_rate

cashflows = total_revenue - annual_opex - annual_debt_interest
cashflows[0] -= total_capex

discounted_cashflows = cashflows / ((1 + discount_rate) ** years)
raw_npv = np.sum(discounted_cashflows)

probability_weighted_itc_value = total_capex * statutory_itc_if_achieved * base_itc_prob
expected_loss = deposit * (1 - permit_prob)

valuation_uplift = 0.0
if valuation_basis == "Levered-lite":
    valuation_uplift = debt_proceeds + tax_equity_proceeds

nu_risk = clamp((nu_cost / 50000000) * 100, 0, 100)
permit_risk = clamp((1 - permit_prob) * 100, 0, 100)
timeline_risk = clamp((timeline_years / 7) * 100, 0, 100)
deposit_risk = clamp((deposit / 5000000) * 100, 0, 100)
itc_risk = clamp((1 - base_itc_prob) * 100, 0, 100)
basis_risk = clamp(abs(min(basis, 0)) / 15 * 100, 0, 100)

risk_score = (
    0.20 * nu_risk +
    0.15 * permit_risk +
    0.15 * timeline_risk +
    0.10 * deposit_risk +
    0.15 * itc_risk +
    0.10 * basis_risk +
    0.15 * safe_harbor_risk
)

risk_score = clamp(risk_score, 0, 100)

risk_factor = 1 - (risk_score / 150)
risk_factor = clamp(risk_factor, 0.25, 1.00)

risk_adjusted_npv = (
    raw_npv
    + probability_weighted_itc_value
    + valuation_uplift
    - expected_loss
) * risk_factor

if risk_adjusted_npv > 150000000:
    economics_score = 90
elif risk_adjusted_npv > 75000000:
    economics_score = 75
elif risk_adjusted_npv > 25000000:
    economics_score = 60
elif risk_adjusted_npv > 0:
    economics_score = 50
else:
    economics_score = 25

decision_score = clamp((0.55 * economics_score) + (0.45 * (100 - risk_score)), 0, 100)

if decision_score >= 70:
    decision = "✅ PROCEED"
    decision_class = "decision-proceed"
elif decision_score >= 50:
    decision = "⚠️ HOLD"
    decision_class = "decision-hold"
else:
    decision = "❌ WITHDRAW"
    decision_class = "decision-withdraw"

# -----------------------------
# EXECUTIVE SUMMARY
# -----------------------------
st.markdown("### Executive Summary")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Decision", decision)
m2.metric("Decision Score", f"{decision_score:.1f}")
m3.metric("Risk Score", f"{risk_score:.1f}")
m4.metric("Risk-Adjusted NPV", fmt_dollar(risk_adjusted_npv))

m5, m6, _ = st.columns([1, 1, 2])
m5.metric("Deposit Loss", fmt_dollar(expected_loss))
m6.metric("ITC Value", fmt_dollar(probability_weighted_itc_value))

st.markdown(
    '<div class="footnote">Risk-Adjusted NPV = (Raw NPV + probability-weighted ITC value + levered-lite proceeds − expected deposit loss) × risk factor.</div>',
    unsafe_allow_html=True
)

# -----------------------------
# SNAPSHOT STRIP
# -----------------------------
st.markdown("### Investment Committee Snapshot")
st.markdown(
    f"""
<span class="pill">Project Type: {project_type}</span>
<span class="pill">Scenario: {scenario}</span>
<span class="pill">Time to COD: {timeline_years} years</span>
<span class="pill">Valuation Basis: {valuation_basis}</span>
<span class="pill">Contract Term: {contract_term_years} years</span>
<span class="pill">Useful Life: {useful_life_years} years</span>
""",
    unsafe_allow_html=True
)

# -----------------------------
# RECOMMENDATION + RISK
# -----------------------------
left, right = st.columns([1.35, 1])

with left:
    st.markdown("### Recommendation")
    st.markdown(
        f"""
<div class="decision-box">
    <div class="{decision_class}">{decision}</div>
    <br>
    <div class="subtle">
        This recommendation reflects projected economics, interconnection capital exposure, permitting confidence,
        tax attribute capture, safe harbor posture, commercial structure, and basis-adjusted merchant pricing assumptions.
    </div>
</div>
""",
        unsafe_allow_html=True
    )

    if scenario_notes:
        st.markdown("### Scenario Notes")
        for note in scenario_notes:
            st.write(f"- {note}")

    st.markdown("### Key Drivers")
    drivers = []

    if risk_adjusted_npv > 0:
        drivers.append("✅ Project remains value-accretive under current assumptions.")
    else:
        drivers.append("⚠️ Risk-adjusted project value is negative under current assumptions.")

    if contract_term_years >= 10:
        drivers.append("✅ Longer contract term reduces exposure to early merchant risk.")
    else:
        drivers.append("⚠️ Shorter contract term pushes merchant exposure earlier in project life.")

    if nu_cost > 25000000:
        drivers.append("⚠️ Network upgrade cost is a major gating item.")
    else:
        drivers.append("✅ Network upgrade cost remains within a more manageable range.")

    if permit_prob < 0.70:
        drivers.append("⚠️ Permitting confidence is below preferred threshold.")
    else:
        drivers.append("✅ Permitting outlook is reasonably supportive.")

    if safe_harbor_status != "Secured":
        drivers.append("⚠️ Safe harbor posture is not fully secured.")
    else:
        drivers.append("✅ Safe harbor posture supports schedule confidence.")

    if schedule_buffer_days < 60:
        drivers.append("⚠️ Schedule buffer to tax deadline is tight.")
    else:
        drivers.append("✅ Schedule buffer is more resilient.")

    if base_itc_prob < 0.80:
        drivers.append("⚠️ ITC capture confidence is below preferred range.")
    else:
        drivers.append("✅ ITC capture confidence supports advancement.")

    if basis < -7:
        drivers.append("⚠️ Basis drag is materially reducing realized merchant pricing.")

    if degradation_rate > 0.0075 and project_type in ["Solar Only", "Solar + BESS"]:
        drivers.append("⚠️ Degradation assumption is meaningfully reducing long-term solar output.")

    if project_type in ["Solar + BESS", "BESS Only"] and bess_margin > 0:
        drivers.append("✅ BESS revenue provides additional commercial support.")

    if valuation_basis == "Levered-lite" and (debt_proceeds > 0 or tax_equity_proceeds > 0):
        drivers.append("✅ Levered-lite basis provides additional capital support at valuation level.")

    for d in drivers:
        st.write(d)

with right:
    st.markdown("### Risk Breakdown")
    risk_df = pd.DataFrame(
        {
            "Category": [
                "NU Risk",
                "Permit Risk",
                "Timeline Risk",
                "Deposit Risk",
                "ITC Risk",
                "Basis Risk",
                "Safe Harbor Risk",
            ],
            "Score": [
                nu_risk,
                permit_risk,
                timeline_risk,
                deposit_risk,
                itc_risk,
                basis_risk,
                safe_harbor_risk,
            ],
        }
    )
    st.bar_chart(risk_df.set_index("Category"))

# -----------------------------
# ECONOMICS
# -----------------------------
st.markdown("### Economics")
er1, er2, er3 = st.columns(3)
with er1:
    card("Raw NPV", fmt_dollar(raw_npv))
with er2:
    card("ITC Value", fmt_dollar(probability_weighted_itc_value))
with er3:
    card("Base Capex", fmt_dollar(base_capex))

er4, er5 = st.columns(2)
with er4:
    card("Annual Opex", fmt_dollar(annual_opex))
with er5:
    card("Capex + NU", fmt_dollar(total_capex), small=True)

# -----------------------------
# SNAPSHOT SECTIONS
# -----------------------------
st.markdown("### Commercial Snapshot")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    card("Contract Term", f"{contract_term_years} yrs", small=True)
with c2:
    card("Useful Life", f"{useful_life_years} yrs", small=True)
with c3:
    card("Contracted Price", f"${contracted_energy_price:,.0f}/MWh", small=True)
with c4:
    card("Merchant Price", f"${base_price:,.0f}/MWh", small=True)
with c5:
    card("Basis", f"${basis:,.0f}/MWh", small=True)

st.markdown("### Tax Attribute / Safe Harbor Snapshot")
x1, x2, x3, x4, x5 = st.columns(5)
with x1:
    card("Statutory ITC", pct(statutory_itc_if_achieved), small=True)
with x2:
    card("ITC Capture", pct(base_itc_prob), small=True)
with x3:
    card("Energy Comm.", pct(energy_community_prob), small=True)
with x4:
    card("Domestic Content", pct(domestic_content_prob), small=True)
with x5:
    card("Buffer", f"{schedule_buffer_days} days", small=True)

st.markdown("### Project Technical Snapshot")
t1, t2, t3, t4, t5 = st.columns(5)
if project_type in ["Solar Only", "Solar + BESS"]:
    with t1:
        card("Solar MWdc", f"{mw_dc:,.0f}", small=True)
    with t2:
        card("Inverter MWac", f"{mw_ac_inv:,.0f}", small=True)
    with t3:
        card("POI MWac", f"{mw_ac_poi:,.0f}", small=True)
    with t4:
        card("Capacity Factor", f"{capacity_factor:.1%}", small=True)
    with t5:
        card("Yr 1 Generation", f"{annual_generation_series[0]:,.0f} MWh", small=True)
else:
    with t1:
        card("BESS MW", f"{bess_power_mw:,.0f}", small=True)
    with t2:
        card("Inverter MWac", "N/A", small=True)
    with t3:
        card("POI MWac", f"{bess_power_mw:,.0f}", small=True)
    with t4:
        card("Capacity Factor", "N/A", small=True)
    with t5:
        card("Yr 1 Generation", "N/A", small=True)

if valuation_basis == "Levered-lite":
    st.markdown("### Levered-lite Snapshot")
    l1, l2, l3 = st.columns(3)
    with l1:
        card("Debt Proceeds", fmt_dollar(debt_proceeds), small=True)
    with l2:
        card("Debt Interest", fmt_dollar(annual_debt_interest), small=True)
    with l3:
        card("Tax Equity", fmt_dollar(tax_equity_proceeds), small=True)

# -----------------------------
# CASHFLOW + TABLE
# -----------------------------
df = pd.DataFrame(
    {
        "Year": years,
        "Revenue Phase": np.where(contract_mask, "Contracted", "Merchant"),
        "Generation (MWh)": annual_generation_series,
        "Merchant Energy Price ($/MWh)": merchant_energy_prices,
        "Effective Merchant Price ($/MWh)": effective_merchant_prices,
        "Contracted Energy Revenue": energy_revenue_contracted,
        "Merchant Energy Revenue": energy_revenue_merchant,
        "Contracted Capacity Revenue": contracted_capacity_revenue,
        "Merchant Capacity Revenue": merchant_capacity_revenue,
        "BESS Revenue": revenue_bess,
        "Total Revenue": total_revenue,
        "Opex": annual_opex,
        "Debt Interest": annual_debt_interest,
        "Cashflow": cashflows,
        "Discounted Cashflow": discounted_cashflows,
    }
)

st.markdown("### Cashflow Profile")
st.line_chart(df.set_index("Year")[["Cashflow", "Discounted Cashflow"]])

st.markdown("### Annual Summary")
display_df = df[[
    "Year",
    "Revenue Phase",
    "Generation (MWh)",
    "Effective Merchant Price ($/MWh)",
    "Contracted Energy Revenue",
    "Merchant Energy Revenue",
    "Total Revenue",
    "Cashflow"
]].copy()

display_df["Generation (MWh)"] = display_df["Generation (MWh)"].map(lambda x: f"{x:,.0f}")
display_df["Effective Merchant Price ($/MWh)"] = display_df["Effective Merchant Price ($/MWh)"].map(lambda x: f"{x:,.2f}")
display_df["Contracted Energy Revenue"] = display_df["Contracted Energy Revenue"].map(fmt_dollar)
display_df["Merchant Energy Revenue"] = display_df["Merchant Energy Revenue"].map(fmt_dollar)
display_df["Total Revenue"] = display_df["Total Revenue"].map(fmt_dollar)
display_df["Cashflow"] = display_df["Cashflow"].map(fmt_dollar)

st.dataframe(display_df, use_container_width=True, height=560)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Annual Summary CSV",
    data=csv,
    file_name="annual_summary.csv",
    mime="text/csv"
)

# -----------------------------
# CHECKLIST
# -----------------------------
st.markdown("### Proceed / Hold Checklist")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.checkbox("Manageable deposit at risk", value=expected_loss < 1000000, disabled=True)
c2.checkbox("ITC confidence acceptable", value=base_itc_prob >= 0.80, disabled=True)
c3.checkbox("Pathway to permit", value=permit_prob >= 0.70, disabled=True)
c4.checkbox("Economics support advancement", value=risk_adjusted_npv > 0, disabled=True)
c5.checkbox("Network cost tolerable", value=nu_cost <= 25000000, disabled=True)
c6.checkbox("Schedule buffer adequate", value=schedule_buffer_days >= 60, disabled=True)

# -----------------------------
# FOOTNOTE
# -----------------------------
st.markdown(
    '<div class="footnote">For academic demonstration only. This tool simplifies project economics, tax attribute capture, commercial structure, degradation, and levered-lite valuation, and is intended as an explainable decision-support layer rather than a full investment model.</div>',
    unsafe_allow_html=True
)