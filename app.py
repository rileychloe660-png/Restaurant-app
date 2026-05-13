# app.py - Upgraded Restaurant Reservation System (Streamlit)

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
import hashlib

# -------------------------------
# CONFIG
# -------------------------------

st.set_page_config(page_title="Restaurant Reservation System", layout="wide")

# -------------------------------
# DATABASE
# -------------------------------

def get_db():
    return sqlite3.connect("restaurant_reservations.db", check_same_thread=False)


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT,
        email TEXT,
        reservation_date TEXT,
        reservation_time TEXT,
        guest_count INTEGER,
        table_number INTEGER,
        status TEXT DEFAULT 'pending',
        special_requests TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tables (
        table_id INTEGER PRIMARY KEY,
        capacity INTEGER,
        is_active INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )""")

    # seed tables
    c.execute("SELECT COUNT(*) FROM tables")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO tables VALUES (?, ?, 1)",
                      [(1,2),(2,2),(3,4),(4,4),(5,6)])

    # seed admin
    c.execute("SELECT COUNT(*) FROM admin_users")
    if c.fetchone()[0] == 0:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO admin_users (username, password_hash) VALUES (?,?)",
                  ("admin", pw))

    conn.commit()
    conn.close()


# -------------------------------
# HELPERS
# -------------------------------

def fetch_reservations():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM reservations ORDER BY id DESC", conn)
    conn.close()
    return df


def insert_reservation(name, phone, email, rdate, rtime, guests, requests):
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reservations
        (customer_name, phone, email, reservation_date, reservation_time, guest_count, special_requests)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, email, str(rdate), str(rtime), guests, requests))

    conn.commit()
    conn.close()


def update_status(res_id, status):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE reservations SET status=? WHERE id=?", (status, res_id))
    conn.commit()
    conn.close()


# -------------------------------
# UI PAGES
# -------------------------------

def home_page():
    st.title("🍽️ Welcome to Our Restaurant")
    st.write("Book your table in seconds.")

    st.divider()

    st.subheader("Make a Reservation")

    with st.form("book_form"):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        rdate = st.date_input("Date")
        rtime = st.time_input("Time")
        guests = st.number_input("Guests", 1, 20)
        requests = st.text_area("Special Requests")

        submit = st.form_submit_button("Reserve Table")

        if submit:
            if name and phone:
                insert_reservation(name, phone, email, rdate, rtime, guests, requests)
                st.success("Reservation confirmed 🎉")
            else:
                st.error("Please fill required fields")


def reservations_page():
    st.title("📋 All Reservations")

    df = fetch_reservations()

    if df.empty:
        st.info("No reservations yet.")
        return

    for _, row in df.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([3,3,2,2])

            with col1:
                st.write(row["customer_name"])
                st.caption(row["phone"])

            with col2:
                st.write(f"{row['reservation_date']} {row['reservation_time']}")
                st.caption(f"{row['guest_count']} guests")

            with col3:
                st.write(row["status"])

            with col4:
                if st.button("Cancel", key=f"cancel_{row['id']}"):
                    update_status(row["id"], "cancelled")
                    st.rerun()


def admin_page():
    st.title("🔐 Admin Dashboard")

    df = fetch_reservations()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Today's Stats")
        st.metric("Total Reservations", len(df))

    with col2:
        st.subheader("Quick Actions")
        if st.button("Clear Cancelled (Demo)"):
            st.success("Action placeholder")

    st.divider()

    st.subheader("All Reservations")
    st.dataframe(df, use_container_width=True)


# -------------------------------
# MAIN APP
# -------------------------------


def main():
    init_db()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    st.sidebar.title("Navigation")

    if st.sidebar.button("🏠 Home"):
        st.session_state.page = "Home"

    if st.sidebar.button("📋 Reservations"):
        st.session_state.page = "Reservations"

    if st.sidebar.button("🔐 Admin"):
        st.session_state.page = "Admin"

    st.sidebar.divider()

    if st.sidebar.button("🔄 Reset View"):
        st.rerun()

    # ROUTER
    if st.session_state.page == "Home":
        home_page()

    elif st.session_state.page == "Reservations":
        reservations_page()

    elif st.session_state.page == "Admin":
        admin_page()


if __name__ == "__main__":
    main()
