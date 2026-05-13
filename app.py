# app.py - Startup-Ready SaaS Restaurant Platform
# Restaurant: Matt Tasty Treats 🍽️
# Fully branded, UI-enhanced, multi-role SaaS system

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# -------------------------------
# CONFIG + BRANDING
# -------------------------------

st.set_page_config(
    page_title="Matt Tasty Treats - Smart Dining SaaS",
    layout="wide",
    page_icon="🍽️"
)

RESTAURANT_NAME = "Matt Tasty Treats"

# -------------------------------
# BEAUTIFUL UI (STARTUP LEVEL STYLING)
# -------------------------------

def load_ui():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)),
        url('https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba');
        background-size: cover;
        background-attachment: fixed;
        color: white;
    }

    .hero {
        text-align: center;
        padding: 40px;
        border-radius: 20px;
        background: rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }

    .title {
        font-size: 48px;
        font-weight: bold;
        color: #f5c542;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.9;
    }

    .card {
        background: rgba(255,255,255,0.08);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        backdrop-filter: blur(10px);
    }

    </style>
    """, unsafe_allow_html=True)


def logo():
    st.markdown("""
    <div style='text-align:center;'>
        <svg width='120' height='120'>
            <circle cx='60' cy='60' r='55' stroke='#f5c542' stroke-width='4' fill='black' />
            <text x='50%' y='55%' text-anchor='middle' fill='#f5c542' font-size='20' font-family='Arial'>MTT</text>
        </svg>
    </div>
    """, unsafe_allow_html=True)


# -------------------------------
# DATABASE
# -------------------------------

def get_db():
    return sqlite3.connect("matt_tasty_treats.db", check_same_thread=False)


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        phone TEXT,
        email TEXT,
        date TEXT,
        time TEXT,
        guests INTEGER,
        table_no INTEGER,
        status TEXT DEFAULT 'pending'
    )""")

    conn.commit()

    # seed admin
    c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if c.fetchone()[0] == 0:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                  ("admin", pw, "admin"))

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
    c.execute("SELECT id, password_hash, role FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user and user[1] == hash_pw(password):
        return {"id": user[0], "role": user[2], "username": username}
    return None


# -------------------------------
# RESERVATION ENGINE
# -------------------------------

def create_reservation(user_id, name, phone, email, date, time, guests):
    conn = get_db()
    c = conn.cursor()

    table_no = (guests % 5) + 1

    c.execute("""
        INSERT INTO reservations (user_id, name, phone, email, date, time, guests, table_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, phone, email, str(date), str(time), guests, table_no))

    conn.commit()
    conn.close()

    return table_no


def fetch_reservations(role, user_id):
    conn = get_db()

    if role == "admin":
        df = pd.read_sql("SELECT * FROM reservations", conn)
    else:
        df = pd.read_sql("SELECT * FROM reservations WHERE user_id=?", conn, params=(user_id,))

    conn.close()
    return df


# -------------------------------
# UI PAGES
# -------------------------------

def landing():
    load_ui()

    logo()

    st.markdown(f"""
    <div class='hero'>
        <div class='title'>{RESTAURANT_NAME}</div>
        <div class='subtitle'>Luxury Dining • Smart Reservations • Premium Experience</div>
    </div>
    """, unsafe_allow_html=True)


def dashboard(user):
    st.sidebar.title("Navigation")

    page = st.sidebar.radio("Go to", ["Home", "My Reservations", "Admin"])

    if page == "Home":
        st.subheader("Book a Table 🍽️")

        with st.form("book"):
            name = st.text_input("Name")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            date = st.date_input("Date")
            time = st.time_input("Time")
            guests = st.number_input("Guests", 1, 20)

            if st.form_submit_button("Reserve"):
                table = create_reservation(user["id"], name, phone, email, date, time, guests)
                st.success(f"Booked at Table {table} 🍽️")

    elif page == "My Reservations":
        st.subheader("Your Bookings")
        df = fetch_reservations(user["role"], user["id"])
        st.dataframe(df, use_container_width=True)

    elif page == "Admin":
        if user["role"] != "admin":
            st.error("Access denied")
        else:
            st.subheader("Admin Control Center")
            df = fetch_reservations("admin", None)

            col1, col2 = st.columns(2)
            col1.metric("Total Bookings", len(df))
            col2.metric("Active", len(df))

            st.dataframe(df, use_container_width=True)


# -------------------------------
# APP
# -------------------------------

def main():
    init_db()

    if "user" not in st.session_state:
        st.title("Login - Matt Tasty Treats")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid login")
        return

    user = st.session_state.user

    dashboard(user)


if __name__ == "__main__":
    main()
