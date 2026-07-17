import os
import json
import sqlite3
import threading
import time
import numpy as np
import pandas as pd
import streamlit as st
from fpdf import FPDF
import pyttsx3
import tempfile
from biomechanics import BiomechanicalEngine
import random
from datetime import datetime

# --- PRODUCTION DASHBOARD SYSTEM INITIALIZATION ---
st.set_page_config(page_title="SportSense AI: Day 3 Telemetry Engine", layout="wide")

DATA_DIR = "data"
REPORTS_DIR = "reports"
ARCHIVES_DIR = "archives" 
SPORTS = ["cricket", "badminton", "tennis", "squash", "weightlifting", "running"]

for d in [DATA_DIR, REPORTS_DIR, ARCHIVES_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

engine = BiomechanicalEngine()

# --- DATABASE SETUP WITH COACH-STUDENT MAPPING ---
def init_db():
    conn = sqlite3.connect("sportsense.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            age INTEGER,
            injury TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            sport TEXT,
            tech_score INTEGER,
            stability_score INTEGER,
            timestamp TEXT,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coach_student_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coach_email TEXT,
            student_email TEXT,
            UNIQUE(coach_email, student_email)
        )
    """)
    try:
        # Default Database Seeds
        cursor.execute("INSERT INTO users (name, email, password, role, age, injury) VALUES (?, ?, ?, ?, ?, ?)",
                       ("Coach Virat", "virat@sportsense.ai", "coach123", "Coach", 35, "None"))
        cursor.execute("INSERT INTO users (name, email, password, role, age, injury) VALUES (?, ?, ?, ?, ?, ?)",
                       ("Coach Dhoni", "dhoni@sportsense.ai", "coach123", "Coach", 42, "None"))
        cursor.execute("INSERT INTO users (name, email, password, role, age, injury) VALUES (?, ?, ?, ?, ?, ?)",
                       ("Pro Athlete", "player@sportsense.ai", "player123", "Player", 19, "None"))
        cursor.execute("INSERT INTO coach_student_mapping (coach_email, student_email) VALUES (?, ?)",
                       ("virat@sportsense.ai", "player@sportsense.ai"))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

init_db()

def get_all_coaches():
    conn = sqlite3.connect("sportsense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, email FROM users WHERE role='Coach'")
    coaches = cursor.fetchall()
    conn.close()
    return coaches

# --- SYSTEM CACHE INITIALIZATION ---
if "tracking_active" not in st.session_state:
    st.session_state["tracking_active"] = False
if "session_completed" not in st.session_state:
    st.session_state["session_completed"] = False
if "last_alert_time" not in st.session_state:
    st.session_state["last_alert_time"] = 0.0

# Session Metadata Buffers
if "saved_tech_score" not in st.session_state:
    st.session_state["saved_tech_score"] = 100
if "saved_stability_score" not in st.session_state:
    st.session_state["saved_stability_score"] = 100
if "saved_error" not in st.session_state:
    st.session_state["saved_error"] = ""
if "saved_video_path" not in st.session_state:
    st.session_state["saved_video_path"] = ""
if "saved_user_report_dir" not in st.session_state:
    st.session_state["saved_user_report_dir"] = REPORTS_DIR
if "session_analytics_cache" not in st.session_state:
    st.session_state["session_analytics_cache"] = {}

def speak_async(text_payload):
    current_time = time.time()
    if current_time - st.session_state["last_alert_time"] < 2.5:
        return
    st.session_state["last_alert_time"] = current_time
    
    def voice_worker(text):
        try:
            voice_engine = pyttsx3.init()
            voice_engine.setProperty('rate', 160)
            voice_engine.say(text)
            voice_engine.runAndWait()
        except Exception:
            pass
    threading.Thread(target=voice_worker, args=(text_payload,), daemon=True).start()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- AUTHENTICATION GATEWAY ---
if not st.session_state["authenticated"]:
    st.title("💪 Welcome to SportSense AI")
    st.markdown("### Initialize your Biomechanical Journey")
    auth_mode = st.radio("Choose Action", ["Sign In / Login", "Create New Account / Register"], horizontal=True)
    
    if auth_mode == "Sign In / Login":
        st.subheader("🔐 Gateway Access Authentication")
        col_user, col_pass = st.columns(2)
        with col_user:
            email_input = st.text_input("Institutional Email Address", value="")
        with col_pass:
            password_input = st.text_input("Security Access Password", type="password", value="")
            
        if st.button("Authorize Control Session", use_container_width=True):
            conn = sqlite3.connect("sportsense.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name, email, role, age, injury FROM users WHERE email=? AND password=?", (email_input, password_input))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                st.session_state["authenticated"] = True
                st.session_state["user_name"] = user_data[0]
                st.session_state["user_email"] = user_data[1]
                st.session_state["user_role"] = user_data[2]
                st.session_state["user_age"] = user_data[3]
                st.session_state["user_injury"] = user_data[4]
                st.success(f"Welcome back, {st.session_state['user_name']}!")
                st.rerun()
            else:
                st.error("Access Denied: Invalid Email Address or Security Password.")
    else:
        st.subheader("📝 Register New Profile")
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Email Address")
            reg_password = st.text_input("Choose Password", type="password")
        with col_reg2:
            reg_role = st.selectbox("Select Account Type / Role", ["Player", "Coach"])
            reg_age = st.slider("Select Current Age", 15, 60, 20)
            reg_injury = st.selectbox("Prior Injury History", ["None", "Lower Back", "Shoulder", "Knee"])
            
            coaches_list = get_all_coaches()
            coach_options = [f"{c[0]} ({c[1]})" for c in coaches_list]
            selected_coach_opt = st.selectbox("Assign Personal Coach / Mentor", coach_options if coach_options else ["No Coach Available"])
            
        if st.button("Register & Create Account", use_container_width=True):
            if reg_name and reg_email and reg_password:
                conn = sqlite3.connect("sportsense.db")
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (name, email, password, role, age, injury) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (reg_name, reg_email, reg_password, reg_role, reg_age, reg_injury))
                    if reg_role == "Player" and coaches_list:
                        selected_coach_email = coaches_list[coach_options.index(selected_coach_opt)][1]
                        cursor.execute("INSERT INTO coach_student_mapping (coach_email, student_email) VALUES (?, ?)", 
                                       (selected_coach_email, reg_email))
                    conn.commit()
                    st.success("🎉 Account created successfully! Proceed to Login.")
                except sqlite3.IntegrityError:
                    st.error("⚠️ Email address already registered.")
                finally:
                    conn.close()

# --- MAIN DASHBOARD INTERFACE ---
else:
    st.title("💪 SportSense AI: Posture Intelligence Dashboard")
    st.sidebar.markdown(f"### 👤 Profile: `{st.session_state['user_name']}`")
    st.sidebar.markdown(f"**Assigned Authority:** `{st.session_state['user_role']}`")
    st.sidebar.markdown(f"**Injury Focus:** `{st.session_state['user_injury']}`")
    
    if st.session_state["user_role"] == "Player":
        conn = sqlite3.connect("sportsense.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT users.name FROM coach_student_mapping 
            JOIN users ON coach_student_mapping.coach_email = users.email 
            WHERE coach_student_mapping.student_email = ?
        """, (st.session_state["user_email"],))
        assigned_coach = cursor.fetchone()
        conn.close()
        if assigned_coach:
            st.sidebar.markdown(f"**⭐ My Coach:** `{assigned_coach[0]}`")

    if st.sidebar.button("Secure Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["session_completed"] = False
        st.rerun()

    tab_live, tab_history, tab_simulator = st.tabs(["🎥 Live Biomechanical Demo", "📂 Performance History Logs", "🎛️ Biomechanics Simulator"])

    with tab_live:
        st.sidebar.header("🎯 Target Parameters")
        selected_sport = st.sidebar.selectbox("Target Discipline", [s.upper() for s in SPORTS]).lower()
        skill_level = st.sidebar.selectbox("Experience Classification", ["Beginner", "Intermediate", "Advanced"])

        st.sidebar.header("📷 Hardware Configuration")
        camera_choice = st.sidebar.selectbox(
            "Select Video Capture Device",
            ["Default In-Built Webcam (Index 0)", "External USB Camera / Input 1 (Index 1)"]
        )
        camera_index = 1 if "Index 1" in camera_choice else 0

        st.subheader(f"Biomechanical Tracking Stream: {selected_sport.upper()}")
        stream_source = st.radio("Choose Performance Feed Source", ["Live Camera Stream", "Upload Practice Video Asset"], horizontal=True)
        
        temp_video_path = None
        if stream_source == "Upload Practice Video Asset":
            uploaded_file = st.file_uploader("Choose an athlete practice video file...", type=["mp4", "mov", "avi"])
            if uploaded_file is not None:
                st.success("🎯 Video asset loaded into buffer cache successfully!")
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                temp_video_path = tfile.name
                tfile.close()

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Start Tracking Session", use_container_width=True, disabled=st.session_state["tracking_active"]):
                if stream_source == "Upload Practice Video Asset" and uploaded_file is None:
                    st.error("Please upload a video file first!")
                else:
                    st.session_state["tracking_active"] = True
                    st.session_state["session_completed"] = False
                    st.rerun()
        with col_btn2:
            if st.button("🛑 Stop & Save Session", use_container_width=True, disabled=not st.session_state["tracking_active"]):
                st.session_state["tracking_active"] = False
                st.session_state["session_completed"] = True
                st.rerun()

        col_stream, col_telemetry = st.columns([2, 1])
        with col_stream:
            video_placeholder = st.empty()
            if not st.session_state["tracking_active"]:
                video_placeholder.info("System Engine idling. Ready to initialize analytical processing loop.")
        with col_telemetry:
            st.markdown("### 📊 Metrics Pipeline")
            score_placeholder = st.empty()
            error_log_placeholder = st.empty()
            injury_matrix_placeholder = st.empty()

        st.markdown("---")
        st.markdown("### 📈 Live Joint Angle Telemetry & Performance Chart")
        graph_placeholder = st.empty()

        # --- LIVE PROCESSING ENGINE LOOP ---
        if st.session_state["tracking_active"]:
            deviation_tracker = []
            angle_history = []
            
            import cv2
            if stream_source == "Upload Practice Video Asset" and temp_video_path is not None:
                cap = cv2.VideoCapture(temp_video_path)
                recording_active = False
            else:
                cap = cv2.VideoCapture(camera_index) 
                recording_active = True
                
            engine.prev_gray = None
            frame_idx = 0

            user_email_str = st.session_state["user_email"] if st.session_state["user_email"] else "anonymous_user"
            clean_email = user_email_str.replace("@", "_").replace(".", "_")
            user_data_dir = os.path.join(DATA_DIR, clean_email)
            user_reports_dir = os.path.join(REPORTS_DIR, clean_email)
            user_archives_dir = os.path.join(ARCHIVES_DIR, clean_email)
            
            for directory in [user_data_dir, user_reports_dir, user_archives_dir]:
                if not os.path.exists(directory):
                    os.makedirs(directory)

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            recorded_file_path = os.path.abspath(os.path.join(user_data_dir, f"session_{selected_sport}_{timestamp_str}.mp4"))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out_writer = None
            
            while cap.isOpened() and st.session_state["tracking_active"]:
                ret, frame = cap.read()
                if not ret:
                    break  
                
                frame = cv2.resize(frame, (640, 480))

                if recording_active:
                    if out_writer is None:
                        out_writer = cv2.VideoWriter(recorded_file_path, fourcc, 20.0, (640, 480))
                    out_writer.write(frame)

                live_angles, frame = engine.extract_live_metrics(frame, selected_sport, frame_idx)
                
                is_posture_faulty = False
                error_string = "Pose parameters tracking inside safe design boundaries."
                injury_profile = "Low Active Musculoskeletal Strain Threat Index."
                line_color = (0, 255, 0)

                threshold_offset = 0
                if skill_level == "Intermediate":
                    threshold_offset = 5
                elif skill_level == "Advanced":
                    threshold_offset = 10

                if selected_sport == "weightlifting":
                    current_angle_val = live_angles.get('weightlifting_spine', 180)
                    if current_angle_val < (168 + threshold_offset):
                        is_posture_faulty = True
                        error_string = f"CRITICAL FAULT: Lumbar spine angle flexed to {current_angle_val}°."
                        injury_profile = f"PATHOLOGICAL RISK: High risk of Lumbar Disc Herniation."
                elif selected_sport == "cricket":
                    current_angle_val = live_angles.get('cricket_head', 170)
                    if current_angle_val < (155 + threshold_offset):
                        is_posture_faulty = True
                        error_string = f"TECHNIQUE FAULT: Cervical head alignment at {current_angle_val}° off-line."
                        injury_profile = "PATHOLOGICAL RISK: High risk of Acute Cervical Facet Strain."
                elif selected_sport == "badminton":
                    current_angle_val = live_angles.get('badminton_smash', 160)
                    if current_angle_val < (152 + threshold_offset):
                        is_posture_faulty = True
                        error_string = f"EXTENSION OVER-INDEX: Kinetic extension angle limited to {current_angle_val}°."
                        injury_profile = "PATHOLOGICAL RISK: High risk of Rotator Cuff Impingement."
                elif selected_sport == "running":
                    current_angle_val = live_angles.get('gait_symmetry', 0)
                    if current_angle_val > (3.5 - (threshold_offset * 0.1)):
                        is_posture_faulty = True
                        error_string = f"GAIT ASYMMETRY: Unilateral deviation tracking at {current_angle_val}°."
                        injury_profile = "PATHOLOGICAL RISK: High risk of IT Band Syndrome."

                deviation_tracker.append(1 if is_posture_faulty else 0)
                angle_history.append(current_angle_val)

                if is_posture_faulty:
                    line_color = (0, 0, 255)
                    speak_async("Warning: Posture Deviation Detected.")

                frame = np.ascontiguousarray(frame)
                cx, cy = 320, 240
                offset = int(10 * np.sin(frame_idx * 0.1))
                cv2.circle(frame, (cx + offset, cy - 80), 20, (255, 255, 255), -1)
                cv2.line(frame, (cx + offset, cy - 55), (cx, cy + 100), line_color, 4)
                cv2.line(frame, (cx + offset, cy - 40), (cx - 60 + offset, cy + 10), line_color, 4)
                cv2.line(frame, (cx + offset, cy - 40), (cx + 60 + offset, cy + 10), line_color, 4)

                video_placeholder.image(frame, channels="BGR", use_container_width=True)

                fault_factor = np.mean(deviation_tracker) if deviation_tracker else 0
                tech_score = int(100 - (fault_factor * 55))
                stability_score = int(100 - (np.std(deviation_tracker) * 40)) if deviation_tracker else 100
                
                with score_placeholder.container():
                    c1, c2 = st.columns(2)
                    c1.metric("📐 Technique Score", f"{tech_score}%")
                    c2.metric("⚖️ Stability Index", f"{stability_score}%")

                error_log_placeholder.info(f"**[{skill_level} Mode] Feedback:**\n\n`{error_string}`")
                if is_posture_faulty:
                    injury_matrix_placeholder.error(f"**Injury Risk Matrix:**\n\n💥 {injury_profile}")
                else:
                    injury_matrix_placeholder.success(f"**Injury Risk Matrix:**\n\n✅ {injury_profile}")

                chart_data = pd.DataFrame({"Frame Timeline": range(len(angle_history)), f"Joint Angle ({selected_sport.upper()})": angle_history}).set_index("Frame Timeline")
                graph_placeholder.line_chart(chart_data)
                
                frame_idx += 1
                time.sleep(0.01)
            
            # --- DAY 3 MATHEMATICAL BREAKDOWN & TELEMETRY ---
            peak_deviation = float(np.max(angle_history) - np.min(angle_history)) if angle_history else 0.0
            consistency_score = int(100 - (np.std(angle_history) * 2)) if angle_history else 100
            consistency_score = max(10, min(100, consistency_score))
            max_strain = float(np.max(angle_history)) if angle_history else 180.0

            analytics_payload = {
                "sport": selected_sport,
                "level": skill_level,
                "tech_score": tech_score,
                "stability_score": stability_score,
                "consistency_score": consistency_score,
                "peak_deviation": round(peak_deviation, 2),
                "max_strain": round(max_strain, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state["session_analytics_cache"] = analytics_payload

            # Archiving
            archive_file_path = os.path.join(user_archives_dir, f"meta_{timestamp_str}.json")
            with open(archive_file_path, "w") as json_file:
                json.dump(analytics_payload, json_file, indent=4)

            st.session_state["saved_tech_score"] = tech_score
            st.session_state["saved_stability_score"] = stability_score
            st.session_state["saved_error"] = error_string
            st.session_state["saved_video_path"] = recorded_file_path if recording_active else ""
            st.session_state["saved_user_report_dir"] = user_reports_dir

            cap.release()
            if out_writer is not None:
                out_writer.release()

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_status = "Excellent" if tech_score > 85 else "Needs Improvement"
            conn = sqlite3.connect("sportsense.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_history (user_email, sport, tech_score, stability_score, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (st.session_state["user_email"], selected_sport.upper(), tech_score, stability_score, current_time, session_status))
            conn.commit()
            conn.close()
            
            st.session_state["tracking_active"] = False
            st.session_state["session_completed"] = True
            st.rerun()

        # --- DAY 3: PERFORMANCE ANALYSIS BREAKDOWN WIDGET ---
        if st.session_state["session_completed"]:
            st.markdown("---")
            st.markdown("## 📊 Session Analytical Performance Breakdown")
            cache = st.session_state["session_analytics_cache"]
            
            if cache:
                # Core Metrics Row Cards
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("🎯 Movement Consistency", f"{cache.get('consistency_score', 100)}%")
                col_m2.metric("📉 Peak Angular Deviation", f"{cache.get('peak_deviation', 0.0)}°")
                col_m3.metric("🔥 Max Joint Strain", f"{cache.get('max_strain', 0.0)}°")
                col_m4.metric("📅 Session Timestamp", f"{cache.get('timestamp', '')}")

                # Visualizing Breakdown Metrics via Dataframe Bar Chart Component
                st.markdown("### 📈 Metric Variances vs. Professional Standards")
                comparison_data = {
                    "Metric Types": ["Consistency Score", "Technique Efficiency", "Stability Index"],
                    "Current Session": [cache.get('consistency_score', 100), cache.get('tech_score', 100), cache.get('stability_score', 100)],
                    "Pro Elite Benchmarks": [90, 95, 92]
                }
                df_compare = pd.DataFrame(comparison_data).set_index("Metric Types")
                st.bar_chart(df_compare)

            st.success("⚙️ Session processed successfully! Generated artifacts are available below:")
            
            if st.session_state["saved_video_path"] and os.path.exists(st.session_state["saved_video_path"]):
                with open(st.session_state["saved_video_path"], "rb") as video_file:
                    st.download_button(label="🎥 Download Your Session Recording", data=video_file, file_name=os.path.basename(st.session_state["saved_video_path"]), mime="video/mp4", use_container_width=True)
            
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", style="B", size=18)
                pdf.cell(200, 10, txt="SportSense AI - Analysis Report Card", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Helvetica", size=12)
                pdf.cell(200, 10, txt=f"Athlete Name: {st.session_state['user_name']}", ln=True)
                pdf.cell(200, 10, txt=f"Sport Category: {selected_sport.upper()}", ln=True)
                pdf.cell(200, 10, txt=f"Level: {skill_level}", ln=True)
                pdf.cell(200, 10, txt=f"Technique Efficiency Score: {st.session_state['saved_tech_score']}%", ln=True)
                pdf.cell(200, 10, txt=f"Overall Stability Matrix Score: {st.session_state['saved_stability_score']}%", ln=True)
                pdf.cell(200, 10, txt=f"Diagnostic Conclusion: {st.session_state['saved_error']}", ln=True)
                
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_output_path = os.path.join(st.session_state["saved_user_report_dir"], f"Report_{selected_sport}_{timestamp_str}.pdf")
                pdf.output(pdf_output_path)
                
                with open(pdf_output_path, "rb") as f:
                    st.download_button("📥 Download Certified Athlete Report Card PDF", data=f, file_name=os.path.basename(pdf_output_path), mime="application/pdf", use_container_width=True)
            except Exception as pdf_error:
                st.error(f"Failed to generate report card: {pdf_error}")

    with tab_history:
        conn = sqlite3.connect("sportsense.db")
        cursor = conn.cursor()
        
        if st.session_state["user_role"] == "Coach":
            st.subheader("📋 Coach Control Command Center")
            cursor.execute("""
                SELECT users.name, users.email, users.age, users.injury 
                FROM coach_student_mapping
                JOIN users ON coach_student_mapping.student_email = users.email
                WHERE coach_student_mapping.coach_email = ?
            """, (st.session_state["user_email"],))
            my_students = cursor.fetchall()
            
            if my_students:
                st.markdown("### 🧑‍🎓 My Assigned Athletes")
                df_students = pd.DataFrame(my_students, columns=["Student Name", "Email Address", "Age", "Injury History"])
                st.table(df_students)
                
                student_emails = [s[1] for s in my_students]
                selected_student = st.selectbox("Select Student to View History Logs", student_emails)
                
                cursor.execute("SELECT id, sport, tech_score, stability_score, timestamp, status FROM performance_history WHERE user_email=? ORDER BY id DESC", (selected_student,))
                history_logs = cursor.fetchall()
                
                if history_logs:
                    df_logs = pd.DataFrame(history_logs, columns=["Session ID", "Sport Discipline", "Technique Score", "Stability Score", "Timestamp", "Performance Status"])
                    st.dataframe(df_logs, use_container_width=True)
                else:
                    st.info("This student hasn't performed any sessions yet.")
            else:
                st.info("You don't have any students assigned to you yet.")
        else:
            st.subheader("📂 My Performance History Log Explorer")
            cursor.execute("SELECT id, user_email, sport, tech_score, stability_score, timestamp, status FROM performance_history WHERE user_email=? ORDER BY id DESC", (st.session_state["user_email"],))
            history_logs = cursor.fetchall()

            if len(history_logs) > 0:
                df_logs = pd.DataFrame(history_logs, columns=["Session ID", "User Email", "Sport Discipline", "Technique Score", "Stability Score", "Timestamp", "Performance Status"])
                st.dataframe(df_logs, use_container_width=True)
                st.line_chart(df_logs[::-1].set_index("Timestamp")["Technique Score"])
            else:
                st.info("No recorded performance logs found yet.")
        conn.close()

    # --- BIOMECH SIMULATOR ---
    with tab_simulator:
        st.subheader("🎛️ Biomechanics Metric & Threshold Simulator")
        sim_sport = st.selectbox("Simulate Sport", SPORTS)
        sim_level = st.radio("Simulate Athlete Level", ["Beginner", "Intermediate", "Advanced"], horizontal=True)
        
        sim_offset = 0
        if sim_level == "Intermediate": sim_offset = 5
        elif sim_level == "Advanced": sim_offset = 10
        
        if sim_sport == "weightlifting":
            angle_val = st.slider("Spine Angle (Degrees)", 130, 180, 170)
            threshold = 168 + sim_offset
            is_fault = angle_val < threshold
            st.metric("Spine Angle Threshold for Fault", f"< {threshold}°")
        elif sim_sport == "cricket":
            angle_val = st.slider("Head Alignment Angle (Degrees)", 130, 180, 160)
            threshold = 155 + sim_offset
            is_fault = angle_val < threshold
            st.metric("Head Angle Threshold for Fault", f"< {threshold}°")
        elif sim_sport == "badminton":
            angle_val = st.slider("Smash Extension Angle (Degrees)", 130, 180, 155)
            threshold = 152 + sim_offset
            is_fault = angle_val < threshold
            st.metric("Extension Threshold for Fault", f"< {threshold}°")
        else:
            angle_val = st.slider("Gait Symmetry Index", 0.0, 10.0, 2.5)
            threshold = 3.5 - (sim_offset * 0.1)
            is_fault = angle_val > threshold
            st.metric("Gait Symmetry Threshold for Fault", f"> {threshold}")

        if is_fault:
            st.error(f"💥 SIMULATOR STATUS: POSTURE FAULT DETECTED FOR {sim_level.upper()} LEVEL!")
        else:
            st.success(f"✅ SIMULATOR STATUS: POSITION SAFE AND OPTIMAL FOR {sim_level.upper()} LEVEL.")