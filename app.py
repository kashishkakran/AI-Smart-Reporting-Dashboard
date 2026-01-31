import streamlit as st
import sqlite3
from datetime import datetime
import os
import random
import openai

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

# streamlit app layout
st.set_page_config(page_title="AI Smart Reporting Dashboard", layout="wide")
st.title("AI-Powered Smart Reporting Dashboard")
st.markdown("Generate structured reports for customer success & solutions consulting.")

# input form
with st.form("report_form"):
    st.subheader("Enter Customer / Project Details")
    customer = st.text_input("Customer Name")
    industry = st.text_input("Industry")
    goals = st.text_area("Goals / Pain Points")

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