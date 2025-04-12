import streamlit as st
import sqlite3
import json
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import threading
import pandas as pd
import time
import queue

# Page configuration
st.set_page_config(
    page_title="Kopitiam Ordering App",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menu items - Singapore Kopitiam Kopi names
COFFEE_MENU = [
    "Kopi", "Kopi O", "Kopi C", "Kopi Siew Dai", "Kopi Po", 
    "Kopi O Kosong", "Kopi Gao", "Kopi Gao Siew Dai", "Kopi Peng", "Kopi O Peng"
]

# Initialize session state variables
def init_session_state():
    if 'current_order' not in st.session_state:
        st.session_state.current_order = []
    if 'order_history' not in st.session_state:
        st.session_state.order_history = []
    if 'listening' not in st.session_state:
        st.session_state.listening = False
    if 'last_speech' not in st.session_state:
        st.session_state.last_speech = ""
    if 'speaking' not in st.session_state:
        st.session_state.speaking = False
    if 'should_rerun' not in st.session_state:
        st.session_state.should_rerun = False
    if 'show_notification' not in st.session_state:
        st.session_state.show_notification = False
    if 'notification_message' not in st.session_state:
        st.session_state.notification_message = ""
    if 'notification_timestamp' not in st.session_state:
        st.session_state.notification_timestamp = 0
    if 'speech_queue' not in st.session_state:
        st.session_state.speech_queue = queue.Queue()
    if "temperature" not in st.session_state:
        st.session_state.temperature = None

# Database setup
def setup_database():
    conn = sqlite3.connect('kopitiam_orders.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS orders
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     items TEXT,
     timestamp TEXT)
    ''')
    conn.commit()
    return conn, c

# Helper functions
def show_notification(message):
    st.session_state.show_notification = True
    st.session_state.notification_message = message
    st.session_state.notification_timestamp = time.time()

def reset_quantities():
    # Reset quantities for all beverages in the current order
    st.session_state.current_order = []

# Fixed text-to-speech function to avoid thread warnings
def speak_text(text):
    st.session_state.speaking = True
    
    # Add the text to the queue instead of starting a thread immediately
    st.session_state.speech_queue.put(text)
    
    # Set flag to rerun the app to trigger the speech handler
    st.session_state.should_rerun = True

# Speech handler that runs in the main thread
def handle_speech_queue():
    if st.session_state.speaking and not st.session_state.speech_queue.empty():
        text = st.session_state.speech_queue.get()
        
        # Run TTS in a thread but don't interact with Streamlit from it
        def tts_thread(text):
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            # Don't set Streamlit variables directly from the thread
        
        thread = threading.Thread(target=tts_thread, args=(text,))
        thread.daemon = True
        thread.start()
        
        # Set a flag to check the thread later
        st.session_state.speaking_thread = thread
    
    # Check if speaking thread is done
    if st.session_state.speaking and hasattr(st.session_state, 'speaking_thread'):
        if not st.session_state.speaking_thread.is_alive():
            st.session_state.speaking = False
            # Remove the thread reference
            delattr(st.session_state, 'speaking_thread')

def recognize_speech():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.session_state.listening = True
            st.rerun()  # Update UI to show listening state
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
    finally:
        st.session_state.listening = False
    
    try:
        text = r.recognize_google(audio)
        st.session_state.last_speech = text
        process_speech_command(text)
        return text
    except Exception as e:
        st.error(f"Sorry, I couldn't understand that. {str(e)}")
        return None

def process_speech_command(text):
    text = text.lower()

    # Determine temperature if mentioned
    temperature = None
    if "hot" in text:
        temperature = "Hot"
    elif "cold" in text or "peng" in text:
        temperature = "Cold"
    else:
        # Default to current temperature setting if not mentioned
        temperature = st.session_state.temperature

    # Check for beverage items in menu
    for beverage in COFFEE_MENU:
        if beverage.lower() in text:
            if temperature:
                add_to_order(beverage, temperature)
                speak_text(f"Added {temperature} {beverage} to your order")
                show_notification(f"✅ Added {temperature} {beverage} to your order")
            else:
                speak_text("Please select hot or cold temperature first")
                show_notification("⚠️ Please select temperature first")
            return

    # Check for order commands
    if any(word in text for word in ["complete", "finish", "place order"]):
        complete_order()
        return

    if any(word in text for word in ["clear", "cancel", "start over"]):
        st.session_state.current_order = []
        reset_quantities()
        speak_text("Order cleared")
        show_notification("🗑️ Order cleared")
        return

    speak_text("I didn't understand your order. Please try again.")

def add_to_order(beverage, temperature=None):
    # Check if the item is already in the order
    for item in st.session_state.current_order:
        if item["beverage"] == beverage and item["temperature"] == temperature:
            # Increment quantity if already in order
            item["quantity"] += 1
            return
    
    # Add as new item if not in order yet
    st.session_state.current_order.append({
        "beverage": beverage,
        "temperature": temperature,
        "quantity": 1
    })

def complete_order():
    if st.session_state.current_order:
        # Save the order to the database
        items_json = json.dumps(st.session_state.current_order)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute("INSERT INTO orders (items, timestamp) VALUES (?, ?)", 
                  (items_json, timestamp))
        conn.commit()
        
        # Add to local history
        st.session_state.order_history.append(list(st.session_state.current_order))
        
        # Clear current order
        st.session_state.current_order = []
        reset_quantities()
        
        speak_text("Order completed")
        show_notification("✅ Order completed and saved")

def load_css():
    st.markdown("""
    <style>
    .floating-notification {
        position: fixed;
        top: 70px;
        right: 20px;
        padding: 15px 20px;
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: fadeInOut 3s forwards;
        max-width: 300px;
    }

    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(20px); }
        10% { opacity: 1; transform: translateY(0); }
        90% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-20px); }
    }

    div.stButton > button {
        width: 100%;
        background-color: #1e1e1e;
        color: white;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 5px;
        font-size: 16px;
        margin: 5px 0;
    }
    div.stButton > button:hover {
        background-color: #333;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #fefbd8 /* Cream color */
    }

    [data-testid="stSidebar"] {
        background-color: #f5e1a4; /* Light beige sidebar */
    }

    [data-testid="stExpander"] {
        background-color: #333 !important;
        color: white !important;
    }

    [data-testid="stExpander"] summary {
        color: white !important;
    }

    /* Fix text color in order history */
    .order-history-text {
        color: white !important;
    }
    
    /* Sidebar menu styling */
    .sidebar-menu-item {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        text-align: center;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .sidebar-menu-item:hover {
        background-color: #e0d084;
    }
    
    .sidebar-menu-item.active {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    
    /* App title styling */
    .app-title {
        color: #333;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #f5e1a4;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Current order styling */
    .order-item {
        display: flex;
        align-items: center;
        padding: 10px;
        margin: 5px 0;
        background-color: #fff;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Category badges */
    .category-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
    }
    
    .coffee-badge {
        background-color: #795548;
        color: white;
    }
    
    /* Temperature indicators */
    .hot-temp {
        color: #f44336;
    }
    
    .cold-temp {
        color: #2196F3;
    }
    </style>
    """, unsafe_allow_html=True)

def display_notification():
    current_time = time.time()
    if st.session_state.show_notification and (current_time - st.session_state.notification_timestamp < 3):
        notification_html = f"""
        <div class="floating-notification">
            {st.session_state.notification_message}
        </div>
        """
        st.markdown(notification_html, unsafe_allow_html=True)
    else:
        st.session_state.show_notification = False

def display_sidebar_menu():
    st.sidebar.markdown("<h2 style='text-align: center; color: black;'>Kopitiam Menu</h2>", unsafe_allow_html=True)
    
    # Kopi menu button
    if st.sidebar.button("☕ Kopi Menu", key="sidebar_coffee"):
        st.session_state.should_rerun = True
    
    # Add a separator
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    
    # Coffee guide
    st.sidebar.markdown("""
    <h3 style="color: black; text-align: center;">Kopi Guide</h3>
    <ul style="color: black;">
        <li><strong>Kopi</strong>: Coffee with condensed milk and sugar</li>
        <li><strong>Kopi O</strong>: Black coffee with sugar</li>
        <li><strong>Kopi C</strong>: Coffee with evaporated milk and sugar</li>
        <li><strong>Kopi Siew Dai</strong>: Coffee with less sugar</li>
        <li><strong>Kopi Po</strong>: Weak coffee with condensed milk</li>
        <li><strong>Kopi O Kosong</strong>: Black coffee without sugar</li>
        <li><strong>Kopi Gao</strong>: Strong coffee</li>
        <li><strong>Kopi Gao Siew Dai</strong>: Strong coffee with less sugar</li>
        <li><strong>Kopi Peng</strong>: Iced coffee with condensed milk</li>
        <li><strong>Kopi O Peng</strong>: Iced black coffee with sugar</li>
    </ul>
    """, unsafe_allow_html=True)

def display_menu(col):
    with col:
        # Menu title
        st.markdown("<h1 style='color: black; text-align: center;'>☕ Kopi Menu</h1>", unsafe_allow_html=True)
        
        # Create a grid layout for menu buttons - 2 columns
        num_cols = 2
        rows = [COFFEE_MENU[i:i + num_cols] for i in range(0, len(COFFEE_MENU), num_cols)]
        
        st.markdown("<h3 style='text-align: center; color: black;'>Select Temperature</h3>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔥 Hot", key="hot_button"):
                st.session_state.temperature = "Hot"

        with col2:
            if st.button("❄️ Cold", key="cold_button"):
                st.session_state.temperature = "Cold"
                
        # Temperature selection feedback and warning
        if st.session_state.temperature == "Hot":
            st.markdown(
                "<p style='color:red; font-weight:bold; text-align:center;'>Hot selected</p>",
                unsafe_allow_html=True,
            )
        elif st.session_state.temperature == "Cold":
            st.markdown(
                "<p style='color:blue; font-weight:bold; text-align:center;'>Cold selected</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<p style='color:black; font-weight:bold; text-align:center;'>Please select Hot or Cold</p>",
                        unsafe_allow_html=True,)

        # Create a table of buttons
        for row in rows:
            cols = st.columns(num_cols)
            for i, beverage in enumerate(row):
                with cols[i]:
                    if st.button(f"Add {beverage}", key=f"add_{beverage}"):
                        if st.session_state.temperature is None:
                            st.warning("Please select Hot or Cold before adding any items.")
                        else:
                            # Add with temperature
                            add_to_order(beverage, st.session_state.temperature)
                            show_notification(f"✅ Added {st.session_state.temperature} {beverage} to your order")
                            st.session_state.should_rerun = True
        
        # Voice input button
        if st.button("Start Voice Input", key="voice_btn"):
            recognize_speech()
            st.session_state.should_rerun = True

def display_order(col):
    with col:
        st.markdown("<h1 style='color: black; text-align: Top;'>Current Order</h1>", unsafe_allow_html=True)
        
        if not st.session_state.current_order:
            st.markdown("<p style='color: black;'>Your order is empty. Add items from the menu or use voice commands.</p>", unsafe_allow_html=True)
        else:
            for i, item in enumerate(st.session_state.current_order):
                cols = st.columns([3, 2, 1])
                
                beverage = item["beverage"]
                quantity = item["quantity"]
                temperature = item.get("temperature", "")
                
                # Format the display name with temperature
                display_name = f"{temperature} {beverage}" if temperature else beverage
                
                # Add temperature styling
                if temperature == "Hot":
                    temp_class = "hot-temp"
                    temp_icon = "🔥"
                elif temperature == "Cold":
                    temp_class = "cold-temp"
                    temp_icon = "❄️"
                else:
                    temp_class = ""
                    temp_icon = ""
                
                cols[0].write(f"<p style='color: black; font-weight: bold;'>{temp_icon} {display_name}</p>", unsafe_allow_html=True)
                cols[1].write(f"<p style='color: black;'>x{quantity}</p>", unsafe_allow_html=True)
                
                # Delete button
                if cols[2].button("🗑️", key=f"remove_item_{i}"):
                    # Remove from order
                    st.session_state.current_order.pop(i)
                    show_notification(f"❌ Removed {display_name} from order")
                    st.session_state.should_rerun = True
                    st.rerun()  # Immediately refresh UI to reflect the change
            
            # Order buttons
            col_clear, col_complete = st.columns(2)
            
            with col_clear:
                if st.button("Clear Order", key="clear_btn"):
                    st.session_state.current_order = []
                    reset_quantities()
                    show_notification("🗑️ Order cleared")
                    st.session_state.should_rerun = True
            
            with col_complete:
                if st.button("✅ Complete Order", key="complete_order"):
                    complete_order()
                    st.session_state.should_rerun = True

def display_order_history():
    st.markdown("<h1 style='color: black; text-align: Top;'>Order History</h1>", unsafe_allow_html=True)

    c.execute("SELECT id, items, timestamp FROM orders ORDER BY timestamp DESC LIMIT 10")
    orders = c.fetchall()
    
    if not orders:
        st.markdown("<p style='color: black;'>No previous orders found.</p>", unsafe_allow_html=True)
    else:
        for order in orders:
            order_id, items_json, timestamp = order
            with st.expander(f"Order #{order_id} - {timestamp}"):
                try:
                    items = json.loads(items_json)
                    if not items:
                        st.markdown("<p class='order-history-text'>Empty order</p>", unsafe_allow_html=True)
                    else:
                        for item in items:
                            beverage = item.get("beverage", "Unknown Beverage")
                            quantity = item.get("quantity", 1)
                            temperature = item.get("temperature", "")
                            
                            display_name = f"{temperature} {beverage}" if temperature else beverage
                            
                            # Add temperature icons
                            if temperature == "Hot":
                                temp_icon = "🔥"
                            elif temperature == "Cold":
                                temp_icon = "❄️"
                            else:
                                temp_icon = ""
                                
                            st.markdown(f"<p class='order-history-text'>{temp_icon} <b>{quantity}x {display_name}</b></p>", unsafe_allow_html=True)
                except json.JSONDecodeError:
                    st.error("Error loading order details.")


def update_sidebar_status():
    # Add speech/listening status to sidebar
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.markdown("<h3>Status</h3>", unsafe_allow_html=True)
    
    if st.session_state.listening:
        st.sidebar.warning("Listening...")
    
    if st.session_state.last_speech:
        st.sidebar.info(f"Last recognized speech: {st.session_state.last_speech}")
    
    if st.session_state.speaking:
        st.sidebar.info("Speaking...")

def main():
    # Initialize our global variables
    init_session_state()
    
    # Handle any pending speech in the queue
    handle_speech_queue()
    
    # Load CSS
    load_css()
    
    # Display application title
    st.markdown("<h1 class='app-title'>Kopi Buddy</h1>", unsafe_allow_html=True)
    
    # Display sidebar menu
    display_sidebar_menu()
    
    # Display notification if active
    display_notification()
    
    # Create layout
    col1, col2 = st.columns([2, 1])
    
    # Display menu in first column
    display_menu(col1)
    
    # Display current order in second column
    display_order(col2)
    
    # Display order history in second column
    with col2:
        display_order_history()
    
    # Update sidebar with speech status
    update_sidebar_status()
    
    # Check if we need to rerun the app
    if st.session_state.should_rerun:
        st.session_state.should_rerun = False
        st.rerun()

# Connect to database
conn, c = setup_database()

if __name__ == "__main__":
    main()
