# app.py - Restaurant Reservation System

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# -------------------------------
# Database Setup
# -------------------------------

def init_database():
    conn = sqlite3.connect('restaurant_reservations.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        reservation_date TEXT NOT NULL,
        reservation_time TEXT NOT NULL,
        guest_count INTEGER NOT NULL,
        table_number INTEGER,
        status TEXT DEFAULT 'pending',
        special_requests TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tables (
        table_id INTEGER PRIMARY KEY,
        capacity INTEGER NOT NULL,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')

    c.execute("SELECT COUNT(*) FROM tables")
    if c.fetchone()[0] == 0:
        default_tables = [(1, 2), (2, 2), (3, 4), (4, 4), (5, 4), (6, 6)]
        c.executemany("INSERT INTO tables (table_id, capacity) VALUES (?, ?)", default_tables)

    c.execute("SELECT COUNT(*) FROM admin_users")
    if c.fetchone()[0] == 0:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)", ("admin", pw))

    conn.commit()
    conn.close()

# -------------------------------
# DB Helpers
# -------------------------------

def get_db_connection():
    return sqlite3.connect('restaurant_reservations.db')

def update_reservation_status(res_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE reservations SET status=? WHERE id=?", (status, res_id))
    conn.commit()
    conn.close()

def get_all_reservations(date_filter=None):
    conn = get_db_connection()
    if date_filter:
        df = pd.read_sql_query(
            "SELECT * FROM reservations WHERE reservation_date=?",
            conn,
            params=(date_filter,)
        )
    else:
        df = pd.read_sql_query("SELECT * FROM reservations", conn)
    conn.close()
    return df

# -------------------------------
# Main UI Fix (CORE PROBLEM AREA)
# -------------------------------

def admin_dashboard():
    st.title("Admin Dashboard")

    tab1, tab2, tab5 = st.tabs(["Today", "Manage", "Reports"])

    with tab2:
        st.markdown("### Manage Tables")

        new_table_id = st.number_input("Table ID", min_value=1, step=1)
        new_capacity = st.number_input("Capacity", min_value=1, step=1)

        if st.button("➕ Add Table"):
            conn = get_db_connection()
            c = conn.cursor()

            c.execute(
                "INSERT OR REPLACE INTO tables (table_id, capacity) VALUES (?, ?)",
                (new_table_id, new_capacity)
            )

            conn.commit()
            conn.close()

            st.success("Table added successfully!")
            st.rerun()

    with tab1:
        st.markdown("### Today's Reservations")

        today = datetime.now().strftime("%Y-%m-%d")
        df_today = get_all_reservations(today)

        if not df_today.empty:
            for _, row in df_today.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2,2,2,1])

                    with col1:
                        st.write(row["customer_name"])
                        st.write(row["phone"])

                    with col2:
                        st.write(row["reservation_time"])
                        st.write(f"{row['guest_count']} guests")

                    with col3:
                        st.write(row["table_number"] or "TBD")

                    with col4:
                        if st.button("Cancel", key=f"c_{row['id']}"):
                            update_reservation_status(row["id"], "cancelled")
                            st.rerun()
        else:
            st.info("No reservations today.")

    with tab5:
        st.markdown("### Reports")

        df = get_all_reservations()

        if not df.empty:
            df["reservation_date"] = pd.to_datetime(df["reservation_date"])
            weekly = df.groupby(df["reservation_date"].dt.isocalendar().week)["id"].count()

            st.bar_chart(weekly)
        else:
            st.info("No data available.")

# -------------------------------
# App Entry
# -------------------------------

def main():
    st.set_page_config(
        page_title="Restaurant Reservation System",
        page_icon="🍽️",
        layout="wide"
    )

    init_database()

    st.sidebar.title("🍽️ Restaurant System")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "📅 Make Reservation",
            "🔍 Check Reservation",
            "❌ Cancel Reservation",
            "🔐 Admin Login"
        ]
    )

    if page == "🏠 Home":
        st.title("🍽️ Restaurant Reservation System")

        st.markdown("""
        Welcome to our restaurant reservation platform.

        Use the sidebar to:
        - Book reservations
        - Check reservation status
        - Cancel reservations
        - Access admin dashboard
        """)

        st.image(
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4",
            use_container_width=True
        )

    elif page == "📅 Make Reservation":
        customer_booking_page()

    elif page == "🔍 Check Reservation":
        check_reservation_status()

    elif page == "❌ Cancel Reservation":
        customer_cancel_page()

    elif page == "🔐 Admin Login":
        admin_login()
