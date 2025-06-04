# bid_tracker_app.py
"""
Streamlit app to track project/bid proposals.
Author: OpenAI Assistant for Ermias Leggesse
Date: 2025-06-04 (rev. 2025-06-04a)

How to deploy on Streamlit Cloud
-------------------------------
1. Create a new GitHub repo and add this file (`bid_tracker_app.py`).
2. Add a `requirements.txt` with **pinned versions** to avoid breaking‑changes:

   ```text
   streamlit==1.34.0
   streamlit-authenticator==0.3.2
   pandas>=2.2
   bcrypt>=4.1
   PyYAML>=6.0
   ```
3. Push to GitHub and on streamlit.io, create a new app from the repo.

Security note: credentials are hard‑coded for demo only; replace with env‑vars or a secrets manager in production.
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
# ----- CONFIGURATION -----------------------------------
# -------------------------------------------------------
APP_TITLE = "📑 Bid / Project Tracker"
DATA_FILE = "projects.csv"

# Single‑user credentials (demo)
NAMES = ["Ermias Leggesse"]
USERNAMES = ["ermias@ketos.co"]
PASSWORDS = ["18221822"]  # replace in prod

# -------------------------------------------------------
# ----- HELPERS -----------------------------------------
# -------------------------------------------------------

def generate_id(length: int = 12) -> str:
    """Random uppercase alphanumeric ID."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def load_data(file_path: str) -> pd.DataFrame:
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    cols = [
        "id",
        "title",
        "status",
        "drive_link",
        "created",
        "last_updated",
        "notes",
    ]
    return pd.DataFrame(columns=cols)


def save_data(df: pd.DataFrame, file_path: str):
    df.to_csv(file_path, index=False)

# -------------------------------------------------------
# ----- AUTHENTICATION (v0.3 API‑safe) ------------------
# -------------------------------------------------------
# The Hasher API changed between versions. The following helper
# adapts automatically so the app keeps working even if the library
# signature shifts again.


def hash_passwords(password_list):
    """Return list of hashed passwords regardless of stauth version."""
    try:
        # Newer (<0.3.0) signature: Hasher().generate(pws)
        return stauth.Hasher().generate(password_list)  # type: ignore[arg-type]
    except TypeError:
        # Older signature: Hasher(pws).generate()
        return stauth.Hasher(password_list).generate()


hashed_passwords = hash_passwords(PASSWORDS)

authenticator = stauth.Authenticate(
    NAMES,
    USERNAMES,
    hashed_passwords,
    "bid_tracker_cookie",
    "abcdef",
    cookie_expiry_days=30,
)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status is False:
    st.error("Username or password is incorrect.")
    st.stop()

if auth_status is None:
    st.warning("Please enter your credentials.")
    st.stop()

# -------------------------------------------------------
# ----- MAIN APP ----------------------------------------
# -------------------------------------------------------

st.set_page_config(page_title=APP_TITLE, layout="wide")
authenticator.logout("Logout", "sidebar")
st.sidebar.success(f"Logged in as {name}")
st.title(APP_TITLE)

# Load / create dataset
projects_df = load_data(DATA_FILE)

# Sidebar navigation
section = st.sidebar.radio("Go to", ["Add / Edit Project", "Dashboard"], label_visibility="collapsed")

# ========== ADD / EDIT SECTION ==========================
if section == "Add / Edit Project":
    st.subheader("➕ Add a New Project / Bid")
    with st.form("project_form", clear_on_submit=True):
        title = st.text_input("Proposal Title", placeholder="e.g., Valley Water Monitoring Grant")
        status = st.selectbox(
            "Current Stage", ["Draft", "Writing", "Submitted", "Awarded", "Closed"], index=1
        )
        drive_link = st.text_input("Google Drive Document Link", placeholder="https://drive.google.com/...")
        notes = st.text_area("Notes / Quick Summary")
        submitted = st.form_submit_button("Save Project")

    if submitted:
        if not title:
            st.error("⚠️ Title is required.")
        else:
            pid = generate_id()
            now_iso = datetime.utcnow().isoformat(timespec="seconds")
            new_row = {
                "id": pid,
                "title": title,
                "status": status,
                "drive_link": drive_link,
                "created": now_iso,
                "last_updated": now_iso,
                "notes": notes,
            }
            projects_df = pd.concat([projects_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(projects_df, DATA_FILE)
            st.success(f"✅ Project {pid} — '{title}' added!")
            st.balloons()

    # Inline editing of saved rows
    if not projects_df.empty:
        st.write("### Existing Projects (click to expand)")
        with st.expander("View / Update Projects"):
            edited_df = st.data_editor(
                projects_df,
                num_rows="dynamic",
                use_container_width=True,
                key="data_editor",
            )
            if st.button("💾 Save Changes to Disk"):
                save_data(edited_df, DATA_FILE)
                projects_df = edited_df  # update in‑memory view too
                st.success("Changes saved.")

# ========== DASHBOARD SECTION ==========================
elif section == "Dashboard":
    st.subheader("📊 Project Dashboard")

    if projects_df.empty:
        st.info("No projects yet. Use 'Add / Edit Project' to create your first record.")
    else:
        # Quick metrics per status
        counts = projects_df["status"].value_counts().sort_index()
        cols = st.columns(len(counts))
        for i, (stat, cnt) in enumerate(counts.items()):
            cols[i].metric(stat, int(cnt))

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            active_status = st.multiselect(
                "Filter by Status", options=projects_df["status"].unique(), default=projects_df["status"].unique()
            )
        with col2:
            query = st.text_input("Search Title / ID")

        view_df = projects_df[projects_df["status"].isin(active_status)].copy()
        if query:
            view_df = view_df[
                view_df["title"].str.contains(query, case=False, na=False)
                | view_df["id"].str.contains(query, case=False, na=False)
            ]

        # Configure link column so it shows as hyperlink in Streamlit 1.34+
        st.dataframe(
            view_df,
            use_container_width=True,
            column_config={"drive_link": st.column_config.LinkColumn("Drive Doc")},
            hide_index=True,
        )

        st.caption("Tip: Click column headers to sort.")
