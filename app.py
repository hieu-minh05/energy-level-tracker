import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as plotly_go
from datetime import date

# --- CONFIG & STYLING ---
st.set_page_config(page_title="EnergyOS", layout="centered", initial_sidebar_state="expanded")

# Minimalist custom CSS to match your aesthetic
st.markdown("""
    <style>
    .stApp { font-family: 'Syne', sans-serif; }
    h1 { font-weight: 700; letter-spacing: -1px; }
    h1 span { color: #e94560; }
    .stButton>button { border-radius: 8px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>Energy<span>OS</span></h1>", unsafe_allow_html=True)
st.caption("Personal Energy Optimization Model — Track sleep, food, and caffeine to predict peak focus hours.")

# --- STATE MANAGEMENT ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Date', 'Hour', 'Energy', 'Sleep', 'SleepQ', 'Bedtime',
        'Caffeine', 'CaffHour', 'Meal', 'Stress', 'Exercise'
    ])
if 'model' not in st.session_state:
    st.session_state.model = None

# --- TABS ---
tab_log, tab_data, tab_schedule = st.tabs(["Log Entry", "Data & Model", "Optimal Schedule"])

# --- 1. LOG ENTRY TAB ---
with tab_log:
    st.subheader("Log today's data")

    col1, col2 = st.columns(2)
    with col1:
        log_date = st.date_input("Date", date.today())
        log_hour = st.selectbox("Time of day", [6, 8, 10, 12, 14, 16, 18, 20], format_func=lambda x: f"{x}:00")
        log_energy = st.slider("Measured energy level (1-10)", 1, 10, 6)

    with col2:
        log_stress = st.slider("Stress level (1-10)", 1, 10, 4)
        log_exercise = st.slider("Exercise today (min)", 0, 120, 0, step=5)

    st.markdown("---")
    st.subheader("Sleep & Nutrition Factors")

    col3, col4, col5 = st.columns(3)
    with col3:
        log_sleep = st.slider("Sleep duration (hrs)", 3.0, 11.0, 7.0, step=0.5)
        log_caff = st.slider("Caffeine today (mg)", 0, 600, 100, step=25)
    with col4:
        log_sleepq = st.slider("Sleep quality (1-10)", 1, 10, 7)
        log_caffhr = st.slider("Caffeine timing (hr)", 5.0, 16.0, 8.0, step=0.5)
    with col5:
        log_bedtime = st.slider("Bedtime hour", 20.0, 26.0, 23.0, step=0.5)
        log_meal = st.slider("Meal quality (1-10)", 1, 10, 6)

    if st.button("➕ Log Entry", use_container_width=True):
        new_entry = pd.DataFrame([{
            'Date': log_date, 'Hour': log_hour, 'Energy': log_energy,
            'Sleep': log_sleep, 'SleepQ': log_sleepq, 'Bedtime': log_bedtime % 24,
            'Caffeine': log_caff, 'CaffHour': log_caffhr, 'Meal': log_meal,
            'Stress': log_stress, 'Exercise': log_exercise
        }])
        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        st.success("Entry logged successfully!")

# --- 2. DATA & MODEL TAB ---
with tab_data:
    df = st.session_state.data

    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("Entries Logged", len(df))
    col_stat2.metric("Avg Energy", f"{df['Energy'].mean():.1f}/10" if not df.empty else "—")

    if st.button("⚙️ Run Regression Model (OLS)", use_container_width=True):
        if len(df) < 5:
            st.error("Need at least 5 entries to fit the model.")
        else:
            # Feature Engineering matching your JS math
            df_model = df.copy()
            df_model['HrSinceCaff'] = np.maximum(0, df_model['Hour'] - df_model['CaffHour'])
            df_model['CaffEffect'] = (df_model['Caffeine'] / 100) * (np.exp(-df_model['HrSinceCaff']/4) - np.exp(-df_model['HrSinceCaff']/1.5) + 0.001)
            df_model['Circadian'] = np.sin((df_model['Hour'] - 6) * np.pi / 12) * 2
            df_model['LowStress'] = 10 - df_model['Stress']
            df_model['ExScaled'] = df_model['Exercise'] / 30

            # Define X and y
            X = df_model[['Sleep', 'SleepQ', 'CaffEffect', 'Meal', 'LowStress', 'ExScaled', 'Circadian']].astype(float)
            X = sm.add_constant(X) # Adds the intercept
            y = df_model['Energy'].astype(float)

            # Fit OLS
            model = sm.OLS(y, X).fit()
            st.session_state.model = model
            st.success(f"Model fitted! R² = {model.rsquared:.3f}")

    if st.session_state.model is not None:
        st.markdown("### Model Coefficients")
        st.dataframe(st.session_state.model.params.rename("Impact Factor").to_frame(), use_container_width=True)

    st.markdown("### Logged Data")
    st.dataframe(df, use_container_width=True)

# --- 3. OPTIMAL SCHEDULE TAB ---
with tab_schedule:
    st.subheader("Predict Your Optimal Day")

    c1, c2, c3, c4 = st.columns(4)
    sch_sleep = c1.number_input("Planned Sleep (hrs)", value=7.5)
    sch_sq = c2.number_input("Est. Sleep Quality", value=7)
    sch_caff = c3.number_input("Planned Caffeine (mg)", value=150)
    sch_caffhr = c4.number_input("Caffeine Time (hr)", value=8.0)

    if st.session_state.model is not None:
        hours = np.arange(6, 22)
        predictions = []

        for h in hours:
            hr_since_caff = max(0, h - sch_caffhr)
            caff_effect = (sch_caff / 100) * (np.exp(-hr_since_caff/4) - np.exp(-hr_since_caff/1.5) + 0.001)
            circadian = np.sin((h - 6) * np.pi / 12) * 2

            # Predict using OLS model
            X_pred = [1.0, sch_sleep, sch_sq, caff_effect, 7.0, 5.0, 0.0, circadian] # Default meal/stress/exercise for projection
            pred_energy = st.session_state.model.predict(X_pred)[0]
            predictions.append(min(10, max(1, pred_energy))) # Clamp between 1 and 10

        # Plotly Bar Chart
        colors = ['#0f9b8e' if p >= 7 else '#f5a623' if p >= 5 else '#e94560' for p in predictions]
        fig = plotly_go.Figure(data=[plotly_go.Bar(
            x=[f"{h}:00" for h in hours],
            y=predictions,
            marker_color=colors,
            marker_line_width=0
        )])
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis=dict(range=[0, 10], gridcolor='rgba(128,128,128,0.2)'),
            xaxis=dict(showgrid=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Syne", color="#888")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log some data and run the model in the 'Data & Model' tab to unlock schedule predictions.")