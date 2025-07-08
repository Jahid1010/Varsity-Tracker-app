import streamlit as st
import pandas as pd
from datetime import datetime, date
import numpy as np

import gspread
from google.oauth2.service_account import Credentials

# -------------------- CONFIG --------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1oX51S8gpH1v-2q_P7DGCezOnXR5tFdJbq8snzr9-9wk/edit#gid=0"
PASSWORD = "Jahid1803105#"

# -------------------- GSPREAD AUTH --------------------
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"]
)
gc = gspread.authorize(creds)
sh = gc.open_by_url(SHEET_URL)
worksheet = sh.sheet1

# -------------------- LOAD / SAVE --------------------
def load_data():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=[
            "Varsity Name", "Subject", "Address", "DAAD Link",
            "Portal Link", "Requriment", "application_through",
            "Summer Start", "Summer Deadline",
            "Winter Start", "Winter Deadline",
            "Deadline", "Done"
        ])
    if "Done" not in df.columns:
        df["Done"] = False
    return df

def save_data(df):
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

data = load_data()

# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="Varsity Tracker", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Entry"

st.sidebar.title("Navigation")
if st.sidebar.button("Entry"):
    st.session_state.page = "Entry"
if st.sidebar.button("List"):
    st.session_state.page = "List"

# -------------------- ENTRY PAGE --------------------
if st.session_state.page == "Entry":
    st.title("🎓 University Entry")

    col1, col2 = st.columns(2)

    with col1:
        varsity_name = st.text_input("Varsity Name")
        daad_link = st.text_input("DAAD Link")
        application_through = st.multiselect(
            "Application Through",
            ["Uni-Assist", "Portal", "Uni-Assist--> Portal"],
            max_selections=1
        )

        enable_summer = st.checkbox("Summer Intake")
        if enable_summer:
            summer_start_date = st.date_input(
                "Summer Start Date",
                value=date(datetime.now().year, 4, 1)
            )
            summer_deadline_date = st.date_input(
                "Summer Deadline",
                value=date(datetime.now().year, 1, 15)
            )
            summer_start = summer_start_date.strftime("%m-%d")
            summer_deadline = summer_deadline_date.strftime("%m-%d")
        else:
            summer_start = ""
            summer_deadline = ""

    with col2:
        subject = st.text_input("Subject")
        portal_link = st.text_input("Portal Link")
        requirement = st.text_input("Requirement")

        enable_winter = st.checkbox("Winter Intake")
        if enable_winter:
            winter_start_date = st.date_input(
                "Winter Start Date",
                value=date(datetime.now().year, 10, 1)
            )
            winter_deadline_date = st.date_input(
                "Winter Deadline",
                value=date(datetime.now().year, 4, 30)
            )
            winter_start = winter_start_date.strftime("%m-%d")
            winter_deadline = winter_deadline_date.strftime("%m-%d")
        else:
            winter_start = ""
            winter_deadline = ""

    address = st.text_input("Address")

    if st.button("Submit"):
        if not varsity_name or not subject:
            st.warning("Varsity Name and Subject are required!")
        elif ((data["Varsity Name"] == varsity_name) & (data["Subject"] == subject)).any():
            st.warning("This varsity and subject already exist.")
        else:
            deadlines = []
            if summer_deadline:
                deadlines.append(datetime.strptime(summer_deadline, "%m-%d"))
            if winter_deadline:
                deadlines.append(datetime.strptime(winter_deadline, "%m-%d"))

            if deadlines:
                earliest_deadline = min(deadlines).strftime("%m-%d")
            else:
                earliest_deadline = ""

            new_row = pd.DataFrame([{
                "Varsity Name": varsity_name,
                "Subject": subject,
                "Address": address,
                "DAAD Link": daad_link,
                "Portal Link": portal_link,
                "Requriment": requirement,
                "application_through": ", ".join(application_through),
                "Summer Start": summer_start,
                "Summer Deadline": summer_deadline,
                "Winter Start": winter_start,
                "Winter Deadline": winter_deadline,
                "Deadline": earliest_deadline,
                "Done": False
            }])
            data = pd.concat([data, new_row], ignore_index=True)
            save_data(data)
            st.success("Entry saved successfully!")
            st.rerun()

# -------------------- LIST PAGE --------------------
elif st.session_state.page == "List":
    st.title("📋 University List")

    if data.empty:
        st.info("No university data available. Please add some from the Entry page.")
    else:
        today = date.today()

        def parse_mmdd(mmdd_str):
            try:
                if not mmdd_str or pd.isna(mmdd_str):
                    return None
                month, day = map(int, mmdd_str.split('-'))
                dt = date(today.year, month, day)
                if dt < today:
                    dt = date(today.year + 1, month, day)
                return dt
            except:
                return None

        data_active = data[data["Done"] == False].copy()

        show_summer = st.checkbox("Show Summer Deadlines", value=True)
        show_winter = st.checkbox("Show Winter Deadlines", value=True)

        if show_summer:
            data_active["Days to Summer"] = data_active["Summer Deadline"].apply(parse_mmdd).apply(
                lambda d: (d - today).days if d else ""
            )
        if show_winter:
            data_active["Days to Winter"] = data_active["Winter Deadline"].apply(parse_mmdd).apply(
                lambda d: (d - today).days if d else ""
            )

        def highlight_deadlines(row):
            summer = row.get("Days to Summer", np.nan)
            winter = row.get("Days to Winter", np.nan)
            if pd.notna(summer) and summer != "" and summer < 25:
                return ['background-color: #ff5959'] * len(row)
            if pd.notna(winter) and winter != "" and winter < 25:
                return ['background-color: #ff5959'] * len(row)
            return [''] * len(row)

        cols_to_show = [
            "Varsity Name", "Subject", "Address", "DAAD Link",
            "Portal Link", "Requriment", "application_through"
        ]
        if show_summer:
            cols_to_show.append("Summer Deadline")
            cols_to_show.append("Days to Summer")
        if show_winter:
            cols_to_show.append("Winter Deadline")
            cols_to_show.append("Days to Winter")

        styled_df = data_active[cols_to_show].style.apply(highlight_deadlines, axis=1)

        st.subheader("📚 Current Applications")
        st.dataframe(styled_df, use_container_width=True)

        st.subheader("✅ Mark as Done")
        for idx, row in data_active.iterrows():
            if st.checkbox(f"{row['Varsity Name']} — {row['Subject']}", key=f"done_{idx}"):
                data.loc[idx, "Done"] = True

        if st.button("💾 Save Done Status"):
            save_data(data)
            st.success("Updated! Checked entries are now marked done and hidden.")
            st.rerun()

        st.markdown("---")
        st.subheader("🧹 Clear All Data")
        with st.form("clear_form"):
            password = st.text_input("Enter password to clear data", type="password")
            confirm_clear = st.form_submit_button("Clear Everything")
            if confirm_clear:
                if password == PASSWORD:
                    data = data.iloc[0:0]
                    save_data(data)
                    st.success("All data cleared!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
