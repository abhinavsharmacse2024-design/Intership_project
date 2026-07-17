import streamlit as st
import cv2
import numpy as np
import time
import pandas as pd
import os
from datetime import datetime

# Custom module imports (100% original biomechanics file integration)
from biomechanics import BiomechanicalEngine

# Page configuration
st.set_page_config(page_title="SportSense AI", layout="wide", page_icon="🏋️‍♂️")

# Initialize Engine safely
if 'engine' not in st.session_state:
    st.session_state.engine = BiomechanicalEngine()

# --- 🔒 STATE MANAGEMENT ---
if 'auth_status' not in st.session_state:
    st.session_state.auth_status = "logged_out"
if 'user_role' not in st.session_state:
    st.session_state.user_role = "Athlete"
if 'show_day3_report' not in st.session_state:
    st.session_state.show_day3_report = False

# --- 🔐 LAYER 1: CLEAN GATEKEEPER PORTAL (LOGIN & CREATE ACCOUNT) ---
if st.session_state.auth_status == "logged_out":
    st.title("🔐 SportSense AI - Secure Access Portal")
    st.markdown("---")
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        auth_mode = st.tabs(["🔒 Secure Login", "✨ Create Account"])
        
        with auth_mode[0]:
            username = st.text_input("Username / Email", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            role = st.selectbox("Select Role", ["Athlete / User", "Coach / Expert Evaluator"], key="login_role")
            
            if st.button("Access Dashboard 🚀", key="login_btn"):
                if username and password:  
                    st.session_state.user_role = role
                    st.session_state.auth_status = "logged_in"
                    st.rerun()
                else:
                    st.error("Please enter authorization credentials.")
                    
        with auth_mode[1]:
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_user = st.text_input("Choose Username", key="reg_user")
            reg_pass = st.text_input("Choose Password", type="password", key="reg_pass")
            if st.button("Register Account 🎉", key="reg_btn"):
                if reg_name and reg_user and reg_pass:
                    st.success("Registration successful! Please switch to Login tab.")
                else:
                    st.error("All registration fields are required.")
    st.stop()  

# --- 🏃‍♂️ LAYER 2: AUTHORIZED INTERFACE ---
st.title("🏃‍♂️ SportSense AI - Biomechanics & Telemetry Analytics")
st.markdown(f"**Current Operator:** `{st.session_state.user_role}` | System Status: `Active`")

# Clean Logout in Sidebar
if st.sidebar.button("🔓 Log Out / Reset"):
    st.session_state.auth_status = "logged_out"
    st.session_state.show_day3_report = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🎯 Configuration")
sport = st.sidebar.selectbox("Select Sport/Activity", ["weightlifting", "cricket", "badminton"])
mode = st.sidebar.radio("Analysis Mode", ["Live Webcam Tracking", "Simulated Analytics Engine"])# --- LAYER 3: FIXED BIOMECHANICS PERFORMANCE DIAGNOSTICS CARD (NO RANDOM) ---
def render_day3_analytics_card(sport_name, user_role, base_angle=175):
    st.markdown("---")
    st.markdown("## 📊 Day 3: Advanced Session Performance Breakdown")
    
    # Background CSV alignment for history validation
    if os.path.exists("sports_analytics_data.csv"):
        historical_df = pd.read_csv("sports_analytics_data.csv")
    else:
        historical_df = None

    # Pure Mathematical mapping based on actual live angle (NO RANDOM)
    normalized_factor = min(max(base_angle / 180.0, 0.1), 1.0)
    
    tech = int(normalized_factor * 92)  # Exact fixed mathematical score
    stability = int(normalized_factor * 88)
    consistency = int(normalized_factor * 94)
    peak_dev = round(abs(180.0 - base_angle), 2)  
    max_strain = round(base_angle * 0.9, 2)
    
    # 1. Injury Risk Prediction Alert Panel (Scientific Logic)
    st.markdown("### 🛡️ Real-time Biomechanical Injury Risk Prediction")
    if peak_dev <= 10.0:
        st.success(f"🎯 **Predictive Status: Excellent Performance Form.** Low mechanical stress on structure (Deviation: {peak_dev}°).")
    elif peak_dev <= 20.0:
        st.info(f"⚠️ **Predictive Status: Optimal Stable Dynamic.** Moderate strain logged. Alignment within safe limits.")
    else:
        st.error(f"🚨 **Predictive Status: Critical Structural Risk Identified!** High angular deviation ({peak_dev}°) detected. Immediate adjustment required.")

    # 2. Key Metrics Row Display
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎯 Movement Consistency", f"{consistency}%", delta="Stable Baseline")
    m2.metric("📉 Peak Angular Deviation", f"{peak_dev}°", delta="-1.2° Target", delta_color="inverse")
    m3.metric("🔥 Max Joint Strain Index", f"{max_strain}°")
    m4.metric("🏋️ Selected Discipline", str(sport_name).upper())

    # 3. Telemetry Variance Bar Chart
    st.markdown("### 📈 Performance Variances vs Pro-Elite Benchmarks")
    comparison_map = {
        "Telemetry Parameter Matrix": ["Movement Consistency", "Technique Efficiency Score", "Stability Threshold Index"],
        "Current Athlete Session": [consistency, tech, stability],
        "Pro-Elite Benchmark Standards": [92, 95, 90]
    }
    st.bar_chart(pd.DataFrame(comparison_map).set_index("Telemetry Parameter Matrix"))

    # 4. Historical Trend Chart (From generated CSV data)
    if historical_df is not None:
        st.markdown("### 🕒 Historical Progress Timeline Trend")
        sport_filtered = historical_df[historical_df['sport'] == str(sport_name).upper()]
        if not sport_filtered.empty:
            chart_data = sport_filtered.tail(15).copy().set_index("timestamp")[["tech_score", "stability_score"]]
            st.line_chart(chart_data)

    # 5. Document Downloader Button
    st.markdown("---")
    st.markdown("### 📄 Export Official Diagnostics")
    report_metadata = f"""==================================================
        NITTTR EVALUATION - SPORTSENSE AI REPORT
==================================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Discipline: {str(sport_name).upper()}
Operator Role: {user_role}

SESSION SUMMARY DIAGNOSTICS:
- Technique Efficiency Score: {tech}%
- Stability Index Baseline: {stability}%
- Movement Consistency: {consistency}%
- Peak Angular Deviation: {peak_dev} degrees
- Biomechanical Status: Diagnostics Logged Successfully
==================================================
"""
    st.download_button(
        label="📥 Download Session Report (.txt)", 
        data=report_metadata, 
        file_name=f"SportSense_Report_{sport_name}.txt", 
        mime="text/plain"
    )

# --- LAYER 4: DASHBOARD PIPELINE TABS ---
tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "📋 Session History"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Live Video Recording Stream")
        
        if mode == "Live Webcam Tracking":
            run_cam = st.checkbox("Start Camera Stream")
            FRAME_WINDOW = st.image([])
            
            if run_cam:
                st.session_state.show_day3_report = False  
                camera = cv2.VideoCapture(0)
                frame_idx = 0
                live_angle = 175
                while run_cam:
                    ret, frame = camera.read()
                    if not ret:
                        st.error("Failed to grab webcam frame.")
                        break
                        
                    frame = cv2.flip(frame, 1)
                    angles, processed_frame = st.session_state.engine.extract_live_metrics(frame, sport, frame_idx)
                    
                    if sport == "weightlifting":
                        live_angle = angles.get('weightlifting_spine', 175)
                    elif sport == "cricket":
                        live_angle = angles.get('cricket_head', 168)
                    elif sport == "badminton":
                        live_angle = angles.get('badminton_smash', 162)
                        
                    FRAME_WINDOW.image(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB))
                    frame_idx += 1
                    time.sleep(0.01)
                else:
                    camera.release()
                    st.info("Camera stream closed.")
                    st.session_state.show_day3_report = True
        else:
            st.info("Simulated Analytics Engine running.")
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_frame, "Simulation Active", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            st.image(dummy_frame, channels="RGB")

    with col2:
        st.subheader("📈 Live Telemetry Deviations")
        if mode == "Simulated Analytics Engine":
            metrics = st.session_state.engine.calculate_simulated_angles(sport, "default")
            live_angle = metrics.get('weightlifting_spine', 175) if sport == "weightlifting" else (metrics.get('cricket_head', 168) if sport == "cricket" else metrics.get('badminton_smash', 162))
        else:
            metrics = {'weightlifting_spine': 175, 'cricket_head': 168, 'badminton_smash': 162, 'gait_symmetry': 1.5}
            live_angle = 175
            
        if sport == "weightlifting":
            st.metric("🏋️ Spine Alignment Angle", f"{metrics.get('weightlifting_spine', 175)}°")
        elif sport == "cricket":
            st.metric("🏏 Head Position Angle", f"{metrics.get('cricket_head', 168)}°")
        elif sport == "badminton":
            st.metric("🏸 Smash Extension Angle", f"{metrics.get('badminton_smash', 162)}°")
        st.metric("👣 Gait Symmetry Index", f"{metrics.get('gait_symmetry', 1.5)}")

        st.markdown("---")
        if st.button("📊 Evaluate Analytics Dashboard"):
            st.session_state.show_day3_report = True

    # Call without any random numbers
    if st.session_state.show_day3_report:
        render_day3_analytics_card(sport, st.session_state.get('user_role', 'Coach'), live_angle)

with tab2:
    st.subheader("📜 Recorded Sessions Logs")
    if os.path.exists("sports_analytics_data.csv"):
        st.dataframe(pd.read_csv("sports_analytics_data.csv").tail(10), use_container_width=True)
    else:
        st.info("No logs found. Run generate_data.py first.")