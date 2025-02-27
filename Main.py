import streamlit as st
import sqlite3
import json
import os
import time
import base64
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import threading
from io import BytesIO
import numpy as np
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Coffee Ordering App",
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

# Database setup
def init_db():
    conn = sqlite3.connect('coffee_orders.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS orders
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     items TEXT,
     total REAL,
     timestamp TEXT)
    ''')
    conn.commit()
    return conn, c

conn, c = init_db()

# Coffee menu
COFFEE_MENU = {
    "Espresso": 2.50,
    "Americano": 3.00,
    "Latte": 3.50,
    "Cappuccino": 3.50,
    "Mocha": 4.00,
    "Flat White": 3.75,
    "Cold Brew": 4.25,
    "Iced Coffee": 3.25,
    "Macchiato": 3.25,
    "Affogato": 4.50
}

# Add-ons
ADD_ONS = {
    "Extra Shot": 0.75,
    "Vanilla Syrup": 0.50,
    "Caramel Syrup": 0.50,
    "Hazelnut Syrup": 0.50,
    "Whipped Cream": 0.50,
    "Almond Milk": 0.75,
    "Oat Milk": 0.75,
    "Soy Milk": 0.75
}

# Speech recognition function
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.session_state.listening = True
        st.experimental_rerun()
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
    
    # Check for coffee orders
    for coffee in COFFEE_MENU:
        if coffee.lower() in text:
            # Check for add-ons
            add_ons = []
            for add_on in ADD_ONS:
                if add_on.lower() in text:
                    add_ons.append(add_on)
            
            # Add to order
            add_to_order(coffee, add_ons)
            speak_text(f"Added {coffee} to your order")
            return
    
    # Check for command to complete order
    if "complete" in text or "finish" in text or "place order" in text:
        complete_order()
        return
    
    # Check for command to clear order
    if "clear" in text or "cancel" in text or "start over" in text:
        st.session_state.current_order = []
        speak_text("Order cleared")
        return
    
    speak_text("I didn't understand your order. Please try again.")

# Text-to-speech function
def speak_text(text):
    def tts_thread(text):
        st.session_state.speaking = True
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        st.session_state.speaking = False
    
    # Run TTS in a separate thread to avoid blocking the UI
    threading.Thread(target=tts_thread, args=(text,)).start()

# Add item to order
def add_to_order(coffee, add_ons=None):
    if add_ons is None:
        add_ons = []
    
    price = COFFEE_MENU[coffee]
    for add_on in add_ons:
        price += ADD_ONS[add_on]
    
    item = {
        "coffee": coffee,
        "add_ons": add_ons,
        "price": price
    }
    
    st.session_state.current_order.append(item)

# Complete order and save to database
def complete_order():
    if not st.session_state.current_order:
        speak_text("Your order is empty")
        return
    
    total = sum(item["price"] for item in st.session_state.current_order)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save to database
    c.execute(
        "INSERT INTO orders (items, total, timestamp) VALUES (?, ?, ?)",
        (json.dumps(st.session_state.current_order), total, timestamp)
    )
    conn.commit()
    
    # Confirmation message
    order_summary = "Order placed successfully. You ordered: "
    for item in st.session_state.current_order:
        coffee = item["coffee"]
        add_ons_text = ", ".join(item["add_ons"]) if item["add_ons"] else "no add-ons"
        order_summary += f"{coffee} with {add_ons_text}, "
    
    order_summary += f"Total: ${total:.2f}"
    speak_text(order_summary)
    
    # Clear current order
    st.session_state.current_order = []

# CSS for floating microphone button
def get_button_css():
    return """
    <style>
    .floating-mic-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #4CAF50;
        color: white;
        text-align: center;
        line-height: 60px;
        font-size: 24px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        z-index: 9999;
        cursor: pointer;
        transition: all 0.3s;
    }
    .floating-mic-button:hover {
        background-color: #45a049;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    }
    .floating-mic-button.listening {
        background-color: #f44336;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    </style>
    """

# Floating microphone button HTML
def get_mic_button_html():
    button_class = "floating-mic-button listening" if st.session_state.listening else "floating-mic-button"
    button_text = "🎤" if not st.session_state.listening else "🔴"
    return f"""
    <div class="{button_class}" onclick="startListening()">
        {button_text}
    </div>
    <script>
    function startListening() {{
        window.parent.postMessage({{type: "streamlit:microphone"}}, "*");
    }}
    </script>
    """

# Main UI
def main():
    st.markdown(get_button_css(), unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("☕ Coffee Ordering App")
        st.markdown("### Speak your order or use the menu below")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Coffee Menu")
        
        # Display menu in a grid
        menu_cols = st.columns(2)
        for i, (coffee, price) in enumerate(COFFEE_MENU.items()):
            with menu_cols[i % 2]:
                st.markdown(f"**{coffee}** - ${price:.2f}")
                
                # Add buttons
                cols = st.columns([3, 1])
                add_ons_selection = cols[0].multiselect(
                    f"Add-ons for {coffee}:",
                    options=list(ADD_ONS.keys()),
                    key=f"add_ons_{coffee}"
                )
                
                if cols[1].button("Add", key=f"add_{coffee}"):
                    add_to_order(coffee, add_ons_selection)
                    st.success(f"Added {coffee} to your order")
        
        st.markdown("---")
        st.subheader("Add-ons")
        
        # Display add-ons in a grid
        add_on_cols = st.columns(2)
        for i, (add_on, price) in enumerate(ADD_ONS.items()):
            with add_on_cols[i % 2]:
                st.markdown(f"**{add_on}** - ${price:.2f}")
    
    with col2:
        st.subheader("Current Order")
        
        if not st.session_state.current_order:
            st.info("Your order is empty. Add items from the menu or use voice commands.")
        else:
            total = 0
            for i, item in enumerate(st.session_state.current_order):
                coffee = item["coffee"]
                price = item["price"]
                add_ons_text = ", ".join(item["add_ons"]) if item["add_ons"] else "No add-ons"
                
                st.markdown(f"**{i+1}. {coffee}** - ${price:.2f}")
                st.markdown(f"   *{add_ons_text}*")
                
                cols = st.columns([1, 1])
                if cols[0].button("Remove", key=f"remove_{i}"):
                    st.session_state.current_order.pop(i)
                    st.experimental_rerun()
                
                total += price
            
            st.markdown("---")
            st.markdown(f"**Total: ${total:.2f}**")
            
            if st.button("Complete Order"):
                complete_order()
                st.success("Order placed successfully!")
                st.experimental_rerun()
            
            if st.button("Clear Order"):
                st.session_state.current_order = []
                st.experimental_rerun()
        
        st.markdown("---")
        st.subheader("Order History")
        
        # Fetch order history from database
        c.execute("SELECT id, items, total, timestamp FROM orders ORDER BY timestamp DESC LIMIT 10")
        orders = c.fetchall()
        
        if not orders:
            st.info("No previous orders found.")
        else:
            for order_id, items_json, total, timestamp in orders:
                with st.expander(f"Order #{order_id} - {timestamp} - ${total:.2f}"):
                    items = json.loads(items_json)
                    for item in items:
                        coffee = item["coffee"]
                        price = item["price"]
                        add_ons_text = ", ".join(item["add_ons"]) if item["add_ons"] else "No add-ons"
                        st.markdown(f"**{coffee}** - ${price:.2f}")
                        st.markdown(f"   *{add_ons_text}*")
    
    # Voice input section
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Voice Commands")
        st.markdown("""
        - Say a coffee name to add it to your order (e.g., "I'd like a Latte")
        - Include add-ons in your order (e.g., "Cappuccino with Vanilla Syrup")
        - Say "complete order" or "place order" to finalize
        - Say "clear order" or "cancel" to start over
        """)
        
        if st.button("Start Voice Input"):
            recognize_speech()
        
        if st.session_state.last_speech:
            st.info(f"Last recognized speech: {st.session_state.last_speech}")
    
    # Floating microphone button
    st.markdown(get_mic_button_html(), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
