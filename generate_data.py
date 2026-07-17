# File: generate_data.py
import pandas as pd
import random
import os
from datetime import datetime, timedelta

def build_project_dataset():
    data = []
    sports = ['CRICKET', 'BADMINTON', 'WEIGHTLIFTING']
    statuses = ['Excellent', 'Optimal', 'Needs Improvement', 'Critical Risk']
    
    start_time = datetime.now() - timedelta(days=30)
    
    for i in range(200):
        sport = random.choice(sports)
        tech_score = random.randint(65, 98)
        stability_score = random.randint(60, 95)
        consistency_score = random.randint(70, 96)
        
        peak_deviation = round(random.uniform(4.0, 18.5), 2)
        max_strain = round(random.uniform(142.0, 175.0), 2)
        
        timestamp = (start_time + timedelta(hours=i*3.5)).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choice(statuses) if tech_score < 85 else 'Excellent'
        
        data.append([sport, tech_score, stability_score, consistency_score, peak_deviation, max_strain, timestamp, status])
        
    columns = ['sport', 'tech_score', 'stability_score', 'consistency_score', 'peak_deviation', 'max_strain', 'timestamp', 'status']
    df = pd.DataFrame(data, columns=columns)
    
    # Forced Current Directory Alignment
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(current_dir, "sports_analytics_data.csv")
    
    df.to_csv(target_path, index=False)
    print(f"✅ Absolute Model Dataset Generated at:\n👉 {target_path}")

if __name__ == "__main__":
    build_project_dataset()