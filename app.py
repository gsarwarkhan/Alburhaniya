import streamlit as st
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import hashlib
from PIL import Image
import os

# Set page configuration
st.set_page_config(
    page_title="Spiritual Tracker",
    page_icon="📿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Database setup with absolute path
db_path = os.path.join(current_dir, "spiritual_tracker.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        is_admin BOOLEAN DEFAULT 0
    )
''')

# Check if activities table exists and has the correct structure
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
if cursor.fetchone():
    # Check if salah_completed column exists
    cursor.execute("PRAGMA table_info(activities)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'salah_completed' not in columns:
        # Create temporary table with new structure
        cursor.execute('''
            CREATE TABLE activities_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                salah_completed BOOLEAN DEFAULT 0,
                al_asaas_count INTEGER DEFAULT 0,
                marboota_shareef_count INTEGER DEFAULT 0,
                fatiha_count INTEGER DEFAULT 0,
                zikr_mufrith_count INTEGER DEFAULT 0,
                notes TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Copy data from old table to new table
        cursor.execute('''
            INSERT INTO activities_new (username, al_asaas_count, marboota_shareef_count, 
                                      fatiha_count, zikr_mufrith_count, notes, date)
            SELECT username, al_asaas_count, marboota_shareef_count, 
                   fatiha_count, zikr_mufrith_count, notes, date
            FROM activities
        ''')
        # Drop old table and rename new table
        cursor.execute("DROP TABLE activities")
        cursor.execute("ALTER TABLE activities_new RENAME TO activities")
else:
    # Create activities table if it doesn't exist
    cursor.execute('''
        CREATE TABLE activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            salah_completed BOOLEAN DEFAULT 0,
            al_asaas_count INTEGER DEFAULT 0,
            marboota_shareef_count INTEGER DEFAULT 0,
            fatiha_count INTEGER DEFAULT 0,
            zikr_mufrith_count INTEGER DEFAULT 0,
            notes TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

# Insert default admin user if not exists
cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
if cursor.fetchone()[0] == 0:
    hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
                  ('admin', hashed_password, 1))
    conn.commit()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to verify password
def verify_password(password, hashed_password):
    return hash_password(password) == hashed_password

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #f8f9fa;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>div>input {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 5px;
        padding: 8px 12px;
    }
    .css-1d391kg {
        padding: 1rem;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stRadio > div {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stNumberInput > div > div > input {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 5px;
    }
    .stTextArea > div > div > textarea {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 5px;
    }
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stAlert {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Load and display logo with absolute path
logo_path = os.path.join(current_dir, "Alburhaniya logo.jpg")
try:
    if os.path.exists(logo_path):
        # Debug information
        st.write(f"Logo path: {logo_path}")
        st.write(f"File exists: {os.path.exists(logo_path)}")
        st.write(f"File size: {os.path.getsize(logo_path)} bytes")
        
        # Load and display logo
        logo = Image.open(logo_path)
        # Center the logo using columns
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image(logo, width=300, use_column_width='auto')
    else:
        st.warning("Logo file not found. Using fallback title.")
        # Create a centered title with emoji when logo is missing
        st.markdown("""
            <div style='text-align: center'>
                <h1>📿 Alburhaniya Spiritual Tracker</h1>
            </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading logo: {str(e)}")
    # Fallback to centered title
    st.markdown("""
        <div style='text-align: center'>
            <h1>📿 Alburhaniya Spiritual Tracker</h1>
        </div>
    """, unsafe_allow_html=True)

# Sidebar login/signup
st.sidebar.title("🔐 Authentication")

# If logged in, show logout button
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.sidebar.success(f"Welcome, {st.session_state['username']}!")
else:
    # Toggle between login and signup
    auth_type = st.sidebar.radio("Choose", ["Login", "Sign Up"])

    if auth_type == "Sign Up":
        st.sidebar.subheader("Create New Account")
        new_username = st.sidebar.text_input("Choose Username")
        new_password = st.sidebar.text_input("Choose Password", type="password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password")
        
        if st.sidebar.button("Sign Up"):
            if not new_username or not new_password:
                st.sidebar.error("Please fill in all fields!")
            elif new_password != confirm_password:
                st.sidebar.error("Passwords do not match!")
            else:
                try:
                    hashed_password = hash_password(new_password)
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                                 (new_username, hashed_password))
                    conn.commit()
                    st.sidebar.success("Account created successfully! Please log in.")
                except sqlite3.IntegrityError:
                    st.sidebar.error("Username already exists!")
    else:
        st.sidebar.subheader("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_button = st.sidebar.button("Login")

        if login_button:
            if not username or not password:
                st.sidebar.error("Please enter both username and password!")
            else:
                cursor.execute("SELECT password, is_admin FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                
                if result and verify_password(password, result[0]):
                    st.sidebar.success(f"Welcome, {username}!")
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["is_admin"] = bool(result[1])
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password.")

# If logged in
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.title("📿 Daily Spiritual Activity Tracker")

    if not st.session_state.get("is_admin", False):  # Normal User Dashboard
        st.subheader("Log Your Spiritual Activity")
        
        # Primary Activity - Salah Prayer
        st.markdown("### 🕌 Primary Activity")
        salah_completed = st.radio("Did you complete all Salah prayers today?", ["Yes", "No"])
        
        # Other Spiritual Activities
        st.markdown("### 📿 Other Spiritual Activities")
        col1, col2 = st.columns(2)
        
        with col1:
            al_asaas_count = st.number_input("Al-Asaas Count", min_value=0, step=1, help="Enter the number of Al-Asaas recitations")
            marboota_shareef_count = st.number_input("Marboota Shareef Count", min_value=0, step=1, help="Enter the number of Marboota Shareef recitations")
        
        with col2:
            fatiha_count = st.number_input("Fatiha Count", min_value=0, step=1, help="Enter the number of Fatiha recitations")
            zikr_mufrith_count = st.number_input("Zikr e Mufrith Count", min_value=0, step=1, help="Enter the number of Zikr e Mufrith recitations")
        
        notes = st.text_area("Additional Notes", help="Add any additional notes about your spiritual activities")

        if st.button("Submit"):
            try:
                cursor.execute('''
                    INSERT INTO activities (username, salah_completed, al_asaas_count, marboota_shareef_count, 
                                          fatiha_count, zikr_mufrith_count, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (st.session_state["username"], salah_completed == "Yes", al_asaas_count, marboota_shareef_count, 
                     fatiha_count, zikr_mufrith_count, notes))
                conn.commit()
                st.success("Your activity has been logged successfully! 📝")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

        # Show user's own activity
        st.subheader("📊 Your Activity History")
        try:
            # Use parameterized query to prevent SQL injection
            df_user = pd.read_sql_query(
                "SELECT * FROM activities WHERE username = ? ORDER BY date DESC",
                conn,
                params=(st.session_state['username'],)
            )
            if not df_user.empty:
                # Format the date column
                df_user['date'] = pd.to_datetime(df_user['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                # Format the boolean column
                df_user['salah_completed'] = df_user['salah_completed'].map({True: 'Yes', False: 'No'})
                # Display the dataframe with better formatting
                st.dataframe(
                    df_user,
                    column_config={
                        "date": st.column_config.DatetimeColumn(
                            "Date",
                            format="YYYY-MM-DD HH:mm:ss"
                        ),
                        "salah_completed": st.column_config.TextColumn(
                            "Salah Completed",
                            help="Whether all Salah prayers were completed"
                        ),
                        "al_asaas_count": st.column_config.NumberColumn(
                            "Al-Asaas Count",
                            help="Number of Al-Asaas recitations"
                        ),
                        "marboota_shareef_count": st.column_config.NumberColumn(
                            "Marboota Shareef Count",
                            help="Number of Marboota Shareef recitations"
                        ),
                        "fatiha_count": st.column_config.NumberColumn(
                            "Fatiha Count",
                            help="Number of Fatiha recitations"
                        ),
                        "zikr_mufrith_count": st.column_config.NumberColumn(
                            "Zikr e Mufrith Count",
                            help="Number of Zikr e Mufrith recitations"
                        ),
                        "notes": st.column_config.TextColumn(
                            "Notes",
                            help="Additional notes about the activities"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No activity data available yet. Start logging your activities!")
        except Exception as e:
            st.error(f"Error loading activity history: {str(e)}")

    else:  # Admin Panel
        st.subheader("📊 Admin Dashboard")
        
        # Admin Password Change Section
        st.subheader("🔐 Change Admin Password")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        if st.button("Change Password"):
            if not current_password or not new_password or not confirm_new_password:
                st.error("Please fill in all password fields!")
            else:
                try:
                    cursor.execute("SELECT password FROM users WHERE username = 'admin'")
                    current_hashed_password = cursor.fetchone()[0]
                    
                    if not verify_password(current_password, current_hashed_password):
                        st.error("Current password is incorrect!")
                    elif new_password != confirm_new_password:
                        st.error("New passwords do not match!")
                    else:
                        new_hashed_password = hash_password(new_password)
                        cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (new_hashed_password,))
                        conn.commit()
                        st.success("Password changed successfully! 🔒")
                except Exception as e:
                    st.error(f"Error changing password: {str(e)}")
        
        # Activity Dashboard
        st.subheader("📊 All Users Activity")
        try:
            df = pd.read_sql_query("SELECT * FROM activities ORDER BY date DESC", conn)
            if not df.empty:
                # Format the date column
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                # Format the boolean column
                df['salah_completed'] = df['salah_completed'].map({True: 'Yes', False: 'No'})
                # Display the dataframe with better formatting
                st.dataframe(
                    df,
                    column_config={
                        "date": st.column_config.DatetimeColumn(
                            "Date",
                            format="YYYY-MM-DD HH:mm:ss"
                        ),
                        "salah_completed": st.column_config.TextColumn(
                            "Salah Completed",
                            help="Whether all Salah prayers were completed"
                        ),
                        "al_asaas_count": st.column_config.NumberColumn(
                            "Al-Asaas Count",
                            help="Number of Al-Asaas recitations"
                        ),
                        "marboota_shareef_count": st.column_config.NumberColumn(
                            "Marboota Shareef Count",
                            help="Number of Marboota Shareef recitations"
                        ),
                        "fatiha_count": st.column_config.NumberColumn(
                            "Fatiha Count",
                            help="Number of Fatiha recitations"
                        ),
                        "zikr_mufrith_count": st.column_config.NumberColumn(
                            "Zikr e Mufrith Count",
                            help="Number of Zikr e Mufrith recitations"
                        ),
                        "notes": st.column_config.TextColumn(
                            "Notes",
                            help="Additional notes about the activities"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No activity data available yet.")
        except Exception as e:
            st.error(f"Error loading activity data: {str(e)}")

        # Visualization
        st.subheader("📈 Activity Analysis")
        
        # Salah Prayer Completion Rate
        st.markdown("### 🕌 Salah Prayer Completion Rate")
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            salah_completion = df.groupby('username')['salah_completed'].mean() * 100
            sns.barplot(x=salah_completion.index, y=salah_completion.values, ax=ax)
            plt.xticks(rotation=45)
            plt.title("Salah Prayer Completion Rate by User (%)")
            plt.ylim(0, 100)
            st.pyplot(fig)
        else:
            st.info("No activity data available yet.")
        
        # Other Activities
        st.markdown("### 📿 Other Activities")
        activities = ['al_asaas_count', 'marboota_shareef_count', 'fatiha_count', 'zikr_mufrith_count']
        activity_names = ['Al-Asaas', 'Marboota Shareef', 'Fatiha', 'Zikr e Mufrith']
        
        if not df.empty:
            for activity, name in zip(activities, activity_names):
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=df["username"], y=df[activity], ax=ax)
                plt.xticks(rotation=45)
                plt.title(f"{name} Count by User")
                st.pyplot(fig)
        else:
            st.info("No activity data available yet.")

else:
    st.warning("Please log in to continue.")