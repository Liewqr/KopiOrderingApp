import streamlit as st
import sqlite3
import json
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import threading

# Set page configuration
st.set_page_config(
    page_title="Kopi Ordering App",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'current_order' not in st.session_state:
    st.session_state.current_order = []
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'last_speech' not in st.session_state:
    st.session_state.last_speech = ""
if 'speaking' not in st.session_state:
    st.session_state.speaking = False
if 'coffee_quantities' not in st.session_state:
    st.session_state.coffee_quantities = {coffee: 0 for coffee in [
        "Espresso", "Americano", "Latte", "Cappuccino", "Mocha",
        "Flat White", "Cold Brew", "Iced Coffee", "Macchiato", "Affogato"
    ]}
if 'should_rerun' not in st.session_state:
    st.session_state.should_rerun = False

# Database setup
def init_db():
    conn = sqlite3.connect('coffee_orders.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS orders
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     items TEXT,
     timestamp TEXT)
    ''')
    conn.commit()
    return conn, c

conn, c = init_db()

# Coffee menu
COFFEE_MENU = [
    "Espresso",
    "Americano",
    "Latte",
    "Cappuccino",
    "Mocha",
    "Flat White",
    "Cold Brew",
    "Iced Coffee",
    "Macchiato",
    "Affogato",
]

# Speech recognition function
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.session_state.listening = True
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
        st.session_state.listening = False
    
    try:
        text = r.recognize_google(audio)
        st.session_state.last_speech = text
        process_speech_command(text)
        return text
    except Exception as e:
        st.error(f"Sorry, I couldn't understand that. {str(e)}")
        return None

# Process speech command
def process_speech_command(text):
    text = text.lower()
    
    for coffee in COFFEE_MENU:
        if coffee.lower() in text:
            add_to_order(coffee)
            speak_text(f"Added {coffee} to your order")
            st.session_state.should_rerun = True
            return
    
    if "complete" in text or "finish" in text or "place order" in text:
        complete_order()
        return
    
    if "clear" in text or "cancel" in text or "start over" in text:
        st.session_state.current_order = []
        reset_quantities()
        speak_text("Order cleared")
        st.session_state.should_rerun = True
        return
    
    speak_text("I didn't understand your order. Please try again.")

# Function to reset quantities
def reset_quantities():
    for coffee in COFFEE_MENU:
        st.session_state.coffee_quantities[coffee] = 0

# Text-to-speech function
def speak_text(text):
    def tts_thread(text):
        st.session_state.speaking = True
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        st.session_state.speaking = False
    
    threading.Thread(target=tts_thread, args=(text,)).start()

# Add item to order
def add_to_order(coffee):
    # Increment quantity in session state
    st.session_state.coffee_quantities[coffee] += 1
    
    # Check if coffee already in order
    for item in st.session_state.current_order:
        if item["coffee"] == coffee:
            item["quantity"] = st.session_state.coffee_quantities[coffee]
            return
    
    # If not, add as new item
    st.session_state.current_order.append({
        "coffee": coffee, 
        "quantity": st.session_state.coffee_quantities[coffee]
    })

# Complete order and save to database
def complete_order():
    if not st.session_state.current_order:
        speak_text("Your order is empty")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute(
        "INSERT INTO orders (items, timestamp) VALUES (?, ?)",
        (json.dumps(st.session_state.current_order), timestamp)
    )
    conn.commit()
    
    order_summary = "Order placed successfully. You ordered: "
    for item in st.session_state.current_order:
        coffee = item["coffee"]
        quantity = item["quantity"]
        order_summary += f"{quantity} {coffee}, "
    
    speak_text(order_summary)
    
    st.session_state.current_order = []
    reset_quantities()
    st.session_state.should_rerun = True

# Main UI
def main():
    st.title("☕ Kopi Ordering App")
    
    # Create a layout with two main columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## Coffee Menu")
        
        # Create a grid layout for coffee buttons - 2 columns
        num_cols = 2
        rows = [COFFEE_MENU[i:i + num_cols] for i in range(0, len(COFFEE_MENU), num_cols)]
        
        # Custom CSS for button styling
        st.markdown("""
        <style>
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
        </style>
        """, unsafe_allow_html=True)
        
        # Create a table of buttons
        for row in rows:
            cols = st.columns(num_cols)
            for i, coffee in enumerate(row):
                with cols[i]:
                    if st.button(f"Add {coffee}", key=f"add_{coffee}"):
                        add_to_order(coffee)
                        st.success(f"Added {coffee} to your order")
                        st.session_state.should_rerun = True
        
        # Voice input button at the bottom of menu
        st.button("Start Voice Input", key="voice_btn", on_click=recognize_speech)
    
    with col2:
        st.markdown("## Current Order")
        
        if not st.session_state.current_order:
            st.info("Your order is empty. Add items from the menu or use voice commands.")
        else:
            # Display current order as a table
            order_table = {
                "Coffee": [],
                "Quantity": []
            }
            
            for item in st.session_state.current_order:
                coffee = item["coffee"]
                quantity = item["quantity"]
                
                order_table["Coffee"].append(coffee)
                order_table["Quantity"].append(quantity)
            
            st.table(order_table)
            
            # Order buttons
            col_clear, col_complete = st.columns(2)
            
            with col_clear:
                if st.button("Clear Order", key="clear_btn"):
                    st.session_state.current_order = []
                    reset_quantities()
                    st.session_state.should_rerun = True
            
            with col_complete:
                if st.button("Place Order", key="place_btn"):
                    complete_order()
        
        st.markdown("## Order History")
        c.execute("SELECT id, items, timestamp FROM orders ORDER BY timestamp DESC LIMIT 10")
        orders = c.fetchall()
        
        if not orders:
            st.info("No previous orders found.")
        else:
            for order in orders:
                order_id, items_json, timestamp = order
                with st.expander(f"Order #{order_id} - {timestamp}"):
                    try:
                        items = json.loads(items_json)
                        for item in items:
                            coffee = item.get("coffee", "Unknown Coffee")
                            quantity = item.get("quantity", 1)
                            st.markdown(f"**{quantity}x {coffee}**")
                    except json.JSONDecodeError:
                        st.error("Error loading order details.")
    
    # Show speech status in sidebar
    if st.session_state.listening:
        st.sidebar.warning("Listening...")
    
    if st.session_state.last_speech:
        st.sidebar.info(f"Last recognized speech: {st.session_state.last_speech}")
    
    if st.session_state.speaking:
        st.sidebar.info("Speaking...")

    # Check if we need to rerun the app
    if st.session_state.should_rerun:
        st.session_state.should_rerun = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
