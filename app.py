import streamlit as st
import sqlite3
from datetime import datetime
import os
import random
import openai
import pandas as pd  
from io import StringIO
import requests

# streamlit app layout
st.set_page_config(page_title="AI Smart Reporting Dashboard", layout="wide")
st.title("AI-Powered Smart Reporting Dashboard")
st.markdown("Generate structured reports for customer success & solutions consulting.")

# openai key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.warning("OPENAI_API_KEY is not set. Please add it in your environment variables / Streamlit Secrets.")
    st.stop()

# database setup
conn = sqlite3.connect("reports.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        industry TEXT,
        goals TEXT,
        report_text TEXT,
        date_created TEXT,
        time_saved REAL,
        quality_score INTEGER
    )
""")
conn.commit()

# load kaggle sample dataset
st.markdown("### Demo Sales Dataset")
try:
    url = "https://raw.githubusercontent.com/kashishkakran/AI-Smart-Reporting-Dashboard/main/sales_data_sample.csv"
    response = requests.get(url)
    if response.status_code == 200:
        sales_data = pd.read_csv(StringIO(response.text))
        # Normalize column names to remove whitespace and ensure consistent casing
        sales_data.columns = [col.strip().upper() for col in sales_data.columns]
        
        st.dataframe(sales_data.head())
        
        # adding a dropdown to select customer from Kaggle data
        selected_customer = st.selectbox("Select a demo customer", sales_data['CUSTOMERNAME'].unique())
        
        if selected_customer:
            demo_row = sales_data[sales_data['CUSTOMERNAME'] == selected_customer].iloc[0]
            demo_industry = demo_row['REGION']  # map Region to Industry
            demo_goals = f"Previous Orders: {demo_row['PRODUCT']} x {demo_row['QUANTITY']}, Total: {demo_row['TOTAL']}"
    else:
        st.warning("Unable to load demo dataset.")
        selected_customer = demo_industry = demo_goals = ""
except Exception as e:
    st.warning(f"Error loading demo dataset: {e}")
    selected_customer = demo_industry = demo_goals = ""

# input form
with st.form("report_form"):
    st.subheader("Enter Customer / Project Details")
    customer = st.text_input("Customer Name", value=selected_customer if selected_customer else "")
    industry = st.text_input("Industry", value=demo_industry if selected_customer else "")
    goals = st.text_area("Goals / Pain Points", value=demo_goals if selected_customer else "")

    submitted = st.form_submit_button("Generate Report")

# ai report generation prompt 
if submitted:
    if customer.strip() == "" or goals.strip() == "":
        st.error("Please fill in at least Customer Name and Goals/Pain Points.")
    else:
        prompt = f"""
You are a Solutions Consultant. Generate a structured report based on the following input:

Customer: {customer}
Industry: {industry}
Goals / Pain Points: {goals}

Include:
1) Summary
2) Next Steps
3) Risks / Challenges
4) Success Metrics

Make it concise and professional.
"""

        with st.spinner("Generating report..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            report_text = response["choices"][0]["message"]["content"]

        st.subheader("Generated Report")
        st.text_area("Report", report_text, height=400)

        #metrics (demo)
        time_saved = round(random.uniform(3, 7), 1)
        quality_score = random.randint(85, 95)

        st.sidebar.metric("Time Saved (hrs)", time_saved)
        st.sidebar.metric("Report Quality Score (%)", quality_score)

        # save to database
        date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
            INSERT INTO reports (customer, industry, goals, report_text, date_created, time_saved, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (customer, industry, goals, report_text, date_created, time_saved, quality_score))

        conn.commit()
        st.success("Report saved to database!")

        # download button
        st.download_button(
            label="Download Report as TXT",
            data=report_text,
            file_name=f"{customer}_report.txt",
            mime="text/plain"
        )

#view past reports
st.subheader("Previous Reports")

c.execute("SELECT customer, industry, date_created, time_saved, quality_score FROM reports ORDER BY date_created DESC")
rows = c.fetchall()

if rows:
    for row in rows:
        st.write(f"**{row[0]}** ({row[1]}) — {row[2]} | Time saved: {row[3]} hrs | Quality: {row[4]}%")
else:
    st.info("No previous reports found.")
