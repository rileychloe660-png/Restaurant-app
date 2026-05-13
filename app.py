# app.py - Production-Level Restaurant Reservation System
# Restaurant: Matt Tasty Treats 🍽️

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
import hashlib

# -------------------------------
# CONFIG
# -------------------------------

st.set_page_config(
    page_title="Matt Tasty Treats - Reservations",
    layout="wide",
    page_icon="🍽️"
)

RESTAURANT_NAME = "Matt Tasty Treats"

# -------------------------------
# DATABASE
# -------------------------------

def get_db():
    return sqlite3.connect("restaurant.db", check_same_thread=False)


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
        c.executemany(
            "INSERT INTO tables VALUES (?, ?, 1)",
            [(1,2),(2,2),(3,4),(4,4),(5,6),(6,8)]
        )

    # seed admin
    c.execute("SELECT COUNT(*) FROM admin_users")
    if c.fetchone()[0] == 0:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (?,?)",
            ("admin", pw)
        )

    conn.commit()
    conn.close()


# -------------------------------
# AUTH
# -------------------------------

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def login(username, password):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admin_users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == hash_pw(password):
        return True
    return False


# -------------------------------
# HELPERS
# -------------------------------

def fetch_reservations():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM reservations ORDER BY reservation_date DESC", conn)
    conn.close()
    return df


def is_slot_taken(rdate, rtime, guests):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM reservations
        WHERE reservation_date=? AND reservation_time=? AND status!='cancelled'
    """, (str(rdate), str(rtime)))
    result = c.fetchone()
    conn.close()
    return result is not None


def insert_reservation(name, phone, email, rdate, rtime, guests, requests):
    conn = get_db()
    c = conn.cursor()

    # simple table assignment
    table_number = (guests % 6) + 1

    c.execute("""
        INSERT INTO reservations
        (customer_name, phone, email, reservation_date, reservation_time, guest_count, table_number, special_requests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, email, str(rdate), str(rtime), guests, table_number, requests))

    conn.commit()
    conn.close()


def update_status(res_id, status):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE reservations SET status=? WHERE id=?", (status, res_id))
    conn.commit()
    conn.close()


# -------------------------------
# UI
# -------------------------------

def home():
    st.title(f"🍽️ Welcome to {RESTAURANT_NAME}")
    st.subheader("Luxury Dining Experience & Easy Reservations")

    st.divider()

    st.header("Book a Table")

    with st.form("booking"):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        rdate = st.date_input("Date")
        rtime = st.time_input("Time")
        guests = st.number_input("Guests", 1, 20)
        requests = st.text_area("Special Requests")

        submit = st.form_submit_button("Reserve Now")

        if submit:
            if is_slot_taken(rdate, rtime, guests):
                st.error("This time slot is already booked. Please choose another.")
            elif not name or not phone:
                st.error("Name and phone are required.")
            else:
                insert_reservation(name, phone, email, rdate, rtime, guests, requests)
                st.success("Reservation confirmed at Matt Tasty Treats 🎉")



def reservations():
    st.title("📋 Reservations")

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
                if st.button("Cancel", key=f"c_{row['id']}"):
                    update_status(row["id"], "cancelled")
                    st.rerun()



def admin():
    st.title("🔐 Admin Dashboard - Matt Tasty Treats")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.session_state.admin = True
        else:
            st.error("Invalid credentials")

    if not st.session_state.get("admin"):
        return

    df = fetch_reservations()

    st.metric("Total Reservations", len(df))

    st.subheader("All Reservations")
    st.dataframe(df, use_container_width=True)

    st.subheader("Analytics")
    if not df.empty:
        chart = df.groupby("reservation_date")["id"].count()
        st.bar_chart(chart)


# -------------------------------
# ROUTER
# -------------------------------

def main():
    init_db()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    st.sidebar.title(RESTAURANT_NAME)

    if st.sidebar.button("Home"):
        st.session_state.page = "Home"

    if st.sidebar.button("Reservations"):
        st.session_state.page = "Reservations"

    if st.sidebar.button("Admin"):
        st.session_state.page = "Admin"

    st.sidebar.divider()

    if st.sidebar.button("Reset"):
        st.rerun()

    if st.session_state.page == "Home":
        home()
    elif st.session_state.page == "Reservations":
        reservations()
    elif st.session_state.page == "Admin":
        admin()


if __name__ == "__main__":
    main()
