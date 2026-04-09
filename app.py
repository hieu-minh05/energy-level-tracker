import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as plotly_go
from datetime import date, datetime
import re

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Energy Level Tracker", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&family=Montserrat:wght@300;400;500&display=swap');
    
    .stApp { 
        background-color: #F4EBE1; 
        color: #33221A; 
        font-family: 'Montserrat', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Cormorant Garamond', serif;
        color: #33221A !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .app-title {
        text-align: center; font-size: 3rem; font-weight: 600; margin-bottom: 0px; padding-bottom: 0px;
    }
    .app-subtitle {
        text-align: center; font-family: 'Cormorant Garamond', serif; font-style: italic; text-transform: lowercase;
        font-size: 1.5rem; color: #5A4435; margin-top: -15px; margin-bottom: 30px;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #FAFCF5; border: 1px solid #D1C7BD; color: #33221A;
    }
    .stButton>button { 
        background-color: #33221A; color: #F4EBE1; border-radius: 4px; 
        font-family: 'Montserrat', sans-serif; font-weight: 500; text-transform: uppercase; border: none;
    }
    .stButton>button:hover { background-color: #5A4435; color: #FFF; }
    label, .stSlider>div>div>div>div {
        color: #33221A !important; font-family: 'Montserrat', sans-serif; font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 class='app-title'>ENERGY LEVEL TRACKER</h1>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>by minh</div>", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Date', 'Time', 'HourFloat', 'Energy', 'Sleep', 'SleepQ',
        'Bedtime', 'CaffeineLog', 'Meal', 'FoodNotes', 'Stress', 'Exercise'
    ])
if 'model' not in st.session_state:
    st.session_state.model = None

# --- HELPER FUNCTIONS ---
def parse_caffeine(caff_str):
    """Parses a string like '08:00=100, 13:30=50' into a list of (hour_float, mg) tuples."""
    coffees = []
    if not caff_str.strip(): return coffees
    entries = caff_str.split(',')
    for entry in entries:
        try:
            time_part, mg_part = entry.split('=')
            hrs, mins = map(int, time_part.strip().split(':'))
            hour_float = hrs + (mins / 60.0)
            mg = float(mg_part.strip())
            coffees.append((hour_float, mg))
        except:
            pass # Ignore malformed entries
    return coffees

def calc_cumulative_caffeine(eval_hour, coffees):
    """Calculates cumulative caffeine effect at eval_hour based on exponential decay."""
    total_effect = 0.0
    for caff_hour, mg in coffees:
        delta_t = eval_hour - caff_hour
        if delta_t > 0:
            # Pharmacokinetic curve approximation (absorption & decay)
            effect = (mg / 100.0) * (np.exp(-delta_t / 4.0) - np.exp(-delta_t / 1.5) + 0.001)
            total_effect += max(0, effect)
    return total_effect

# --- TABS ---
tab_log, tab_data, tab_schedule = st.tabs(["Log Entry", "Data & Model", "Optimal Schedule"])

# --- 1. LOG ENTRY TAB ---
with tab_log:
    st.markdown("### Log Your Current State")

    col1, col2 = st.columns(2)
    with col1:
        log_date = st.date_input("Date", date.today())
        log_time = st.time_input("Exact Time", datetime.now().time())
        log_energy = st.slider("Energy level right now (1-10)", 1, 10, 6)

    with col2:
        log_stress = st.slider("Stress level (1-10)", 1, 10, 4)
        log_exercise = st.slider("Exercise today (min)", 0, 120, 0, step=5)

    st.markdown("---")
    st.markdown("### Sleep, Nutrition & Coffee")

    col3, col4 = st.columns(2)
    with col3:
        log_sleep = st.slider("Sleep duration (hrs)", 3.0, 11.0, 7.0, step=0.5)
        log_bedtime = st.slider("Bedtime hour (24h)", 20.0, 26.0, 23.0, step=0.5)
    with col4:
        log_sleepq = st.slider("Sleep quality (1-10)", 1, 10, 7)
        log_meal = st.slider("Meal quality (1-10)", 1, 10, 6)

    st.markdown("### Caffeine Intake")
    log_caff_str = st.text_input(
        "Log all coffees today (Format: HH:MM=mg, comma separated)",
        value="08:00=100, 13:00=50",
        help="Example: '08:00=100, 14:30=50' means 100mg at 8am and 50mg at 2:30pm"
    )

    st.markdown("### Food & Body Notes")
    log_food_notes = st.text_area(
        "Notes on food volume, carbs, digestion, or how you feel:",
        placeholder="e.g., Ate a heavy pasta lunch, feeling brain fog and sluggish..."
    )

    if st.button("➕ Save Entry", use_container_width=True):
        hour_float = log_time.hour + log_time.minute / 60.0

        new_entry = pd.DataFrame([{
            'Date': log_date, 'Time': log_time.strftime("%H:%M"), 'HourFloat': hour_float,
            'Energy': log_energy, 'Sleep': log_sleep, 'SleepQ': log_sleepq,
            'Bedtime': log_bedtime % 24, 'CaffeineLog': log_caff_str,
            'Meal': log_meal, 'FoodNotes': log_food_notes, 'Stress': log_stress, 'Exercise': log_exercise
        }])
        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        st.success("Entry logged beautifully!")

# --- 2. DATA & MODEL TAB ---
with tab_data:
    df = st.session_state.data

    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("Entries Logged", len(df))
    col_stat2.metric("Avg Energy", f"{df['Energy'].mean():.1f}/10" if not df.empty else "—")

    if st.button("⚙️ Run Optimization Model", use_container_width=True):
        if len(df) < 5:
            st.error("Need at least 5 entries to find patterns.")
        else:
            df_model = df.copy()

            # Apply cumulative caffeine math to historical data
            df_model['CaffEffect'] = df_model.apply(
                lambda row: calc_cumulative_caffeine(row['HourFloat'], parse_caffeine(row['CaffeineLog'])),
                axis=1
            )

            df_model['Circadian'] = np.sin((df_model['HourFloat'] - 6) * np.pi / 12) * 2
            df_model['LowStress'] = 10 - df_model['Stress']
            df_model['ExScaled'] = df_model['Exercise'] / 30

            X = df_model[['Sleep', 'SleepQ', 'CaffEffect', 'Meal', 'LowStress', 'ExScaled', 'Circadian']].astype(float)
            X = sm.add_constant(X)
            y = df_model['Energy'].astype(float)

            model = sm.OLS(y, X).fit()
            st.session_state.model = model
            st.success(f"Model trained! Variance explained: {model.rsquared*100:.1f}%")

    st.markdown("### Your Logbook")
    display_cols = ['Date', 'Time', 'Energy', 'CaffeineLog', 'FoodNotes']
    if not df.empty:
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.info("Your logbook is empty.")

# --- 3. OPTIMAL SCHEDULE TAB ---
with tab_schedule:
    st.markdown("### Predict Your Optimal Day")

    c1, c2, c3 = st.columns(3)
    sch_sleep = c1.number_input("Planned Sleep (hrs)", value=7.5)
    sch_sq = c2.number_input("Est. Sleep Quality", value=7)
    sch_meal = c3.number_input("Est. Meal Quality", value=7)

    sch_caff_str = st.text_input("Planned Coffees (Format: HH:MM=mg)", value="08:00=100, 13:00=50")

    if st.session_state.model is not None:
        hours = np.arange(6, 22)
        predictions = []
        planned_coffees = parse_caffeine(sch_caff_str)

        for h in hours:
            caff_effect = calc_cumulative_caffeine(h, planned_coffees)
            circadian = np.sin((h - 6) * np.pi / 12) * 2

            X_pred = [1.0, sch_sleep, sch_sq, caff_effect, sch_meal, 5.0, 0.0, circadian]
            pred_energy = st.session_state.model.predict(X_pred)[0]
            predictions.append(min(10, max(1, pred_energy)))

        colors = ['#33221A' if p >= 7 else '#8C7A6B' if p >= 5 else '#D1C7BD' for p in predictions]
        fig = plotly_go.Figure(data=[plotly_go.Bar(
            x=[f"{h}:00" for h in hours],
            y=predictions,
            marker_color=colors,
            marker_line_width=0
        )])
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis=dict(range=[0, 10], gridcolor='rgba(51,34,26,0.1)'),
            xaxis=dict(showgrid=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Montserrat", color="#33221A")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log some data and run the model in the 'Data & Model' tab to unlock schedule predictions.")