# bid_tracker_app.py
"""
Streamlit app to track project/bid proposals.
Author: OpenAI Assistant for Ermias Leggesse
Date: 2025‑06‑04

How to deploy on Streamlit Cloud
-------------------------------
1. Create a new GitHub repo and add this file (`bid_tracker_app.py`)
2. Add a `requirements.txt` with:
   streamlit
   streamlit-authenticator
   pandas
   bcrypt
   PyYAML
3. Push to GitHub and on streamlit.io, create a new app from the repo.
4. That's it!  Streamlit Cloud will install requirements and start the app.

Security Note
-------------
- This demo uses a single hard‑coded username/password.
- For real-world use, consider env vars or a secrets manager.
"""

from __future__ import annotations
import os
import random
import string
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth

# -------------------------------------------------------
# ----- CONFIGURATION SECTION ---------------------------
# -------------------------------------------------------

APP_TITLE = "📑 Bid / Project Tracker"
DATA_FILE = "projects.csv"

# Single‑user credentials
NAMES = ['Ermias Leggesse']
USERNAMES = ['ermias@ketos.co']
PASSWORDS = ['18221822']   # <-- plaintext just for demo. Change in production!

# -------------------------------------------------------
# ----- HELPER FUNCTIONS --------------------------------
# -------------------------------------------------------

def generate_id(length: int = 12) -> str:
    """Generate a random uppercase alphanumeric ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def load_data(file_path: str) -> pd.DataFrame:
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    cols = ['id', 'title', 'status', 'drive_link', 'created', 'last_updated', 'notes']
    return pd.DataFrame(columns=cols)


def save_data(df: pd.DataFrame, file_path: str):
    df.to_csv(file_path, index=False)

# -------------------------------------------------------
# ----- AUTHENTICATION ----------------------------------
# -------------------------------------------------------

hashed_passwords = stauth.Hasher(PASSWORDS).generate()

authenticator = stauth.Authenticate(
    NAMES,
    USERNAMES,
    hashed_passwords,
    "bid_tracker_cookie",
    "abcdef",
    cookie_expiry_days=30
)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status is False:
    st.error("Username/password is incorrect")

if auth_status is None:
    st.warning("Please enter your username and password.")

# -------------------------------------------------------
# ----- MAIN APP (requires successful login) ------------
# -------------------------------------------------------
if auth_status:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")
    st.title(APP_TITLE)

    # Load existing data
    df = load_data(DATA_FILE)

    # Sidebar navigation
    menu_choice = st.sidebar.radio("Go to", ["Add / Edit Project", "Dashboard"], label_visibility="collapsed")

    # ------------------ ADD / EDIT ---------------------
    if menu_choice == "Add / Edit Project":
        st.subheader("➕ Add a New Project / Bid")
        with st.form("project_form", clear_on_submit=True):
            title = st.text_input("Proposal Title", placeholder="e.g., Valley Water Monitoring Grant")
            status = st.selectbox("Current Stage", ["Draft", "Writing", "Submitted", "Awarded", "Closed"], index=1)
            drive_link = st.text_input("Google Drive Document Link", placeholder="https://drive.google.com/...")

            notes = st.text_area("Notes / Quick Summary")
            submitted = st.form_submit_button("Save Project")

        if submitted:
            if not title:
                st.error("⚠️ Title is required.")
            else:
                new_id = generate_id()
                now = datetime.utcnow().isoformat(timespec='seconds')
                new_entry = {
                    "id": new_id,
                    "title": title,
                    "status": status,
                    "drive_link": drive_link,
                    "created": now,
                    "last_updated": now,
                    "notes": notes
                }
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                save_data(df, DATA_FILE)
                st.success(f"✅ Project {new_id} — '{title}' added!")
                st.balloons()

        if not df.empty:
            st.write("### Existing Projects (click to expand)")
            with st.expander("View / Update Projects"):
                editable_df = st.data_editor(
                    df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="data_editor"
                )
                if st.button("💾 Save Changes to Disk"):
                    save_data(editable_df, DATA_FILE)
                    st.success("All changes saved!")

    # ------------------ DASHBOARD ---------------------
    elif menu_choice == "Dashboard":
        st.subheader("📊 Project Dashboard")

        if df.empty:
            st.info("No projects yet. Use 'Add / Edit Project' to create your first record.")
        else:
            # Quick stats
            status_counts = df['status'].value_counts().sort_index()
            cols = st.columns(len(status_counts))
            for i, (stat, cnt) in enumerate(status_counts.items()):
                cols[i].metric(stat, cnt)

            # Filter widgets
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect("Filter by Status", options=df['status'].unique(),
                                               default=df['status'].unique())
            with col2:
                search_term = st.text_input("Search Title / ID")

            filtered_df = df[df['status'].isin(status_filter)]
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['title'].str.contains(search_term, case=False, na=False) |
                    filtered_df['id'].str.contains(search_term, case=False, na=False)
                ]

            # Display table with clickable links
            st.dataframe(
                filtered_df,
                use_container_width=True,
                column_config={
                    "drive_link": st.column_config.LinkColumn("Drive Doc")
                },
                hide_index=True
            )

            st.caption("Tip: Click column headers to sort.")
