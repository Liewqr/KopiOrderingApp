import streamlit as st
import sqlite3
import json
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import threading
import pandas as pd
import time

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
# Add notification state variables
if 'show_notification' not in st.session_state:
    st.session_state.show_notification = False
if 'notification_message' not in st.session_state:
    st.session_state.notification_message = ""
if 'notification_timestamp' not in st.session_state:
    st.session_state.notification_timestamp = 0

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

# Function to display notification
def show_notification(message):
    st.session_state.show_notification = True
    st.session_state.notification_message = message
    st.session_state.notification_timestamp = time.time()

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
            show_notification(f"✅ Added {coffee} to your order")
            st.session_state.should_rerun = True
            return
    
    if "complete" in text or "finish" in text or "place order" in text:
        complete_order()
        return
    
    if "clear" in text or "cancel" in text or "start over" in text:
        st.session_state.current_order = []
        reset_quantities()
        speak_text("Order cleared")
        show_notification("🗑️ Order cleared")
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
        show_notification("⚠️ Your order is empty")
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
    show_notification("🎉 Order placed successfully!")
    
    st.session_state.current_order = []
    reset_quantities()
    st.session_state.should_rerun = True

# Main UI
def main():
    st.markdown("""
    <h1 style='color: black; text-align: center;'>☕ Kopi Ordering App</h1>""", unsafe_allow_html=True)
    
    
    # Add CSS for floating notification
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
    background-color: #fefbd8 /* Cream color*/
    }

    [data-testid='stSidebar"] {
        background-color: #f5e1a4; /* Light beige sidebar */
        }
    
    

    </style>
    """, unsafe_allow_html=True)
    
    # Display floating notification if active
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
    
    # Create a layout with two main columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <h1 style='color: black; text-align: Top ;'>Coffee Menu</h1>""", unsafe_allow_html=True)
        
        # Create a grid layout for coffee buttons - 2 columns
        num_cols = 2
        rows = [COFFEE_MENU[i:i + num_cols] for i in range(0, len(COFFEE_MENU), num_cols)]
        
        # Create a table of buttons
        for row in rows:
            cols = st.columns(num_cols)
            for i, coffee in enumerate(row):
                with cols[i]:
                    if st.button(f"Add {coffee}", key=f"add_{coffee}"):
                        add_to_order(coffee)
                        show_notification(f"✅ Added {coffee} to your order")
                        st.session_state.should_rerun = True
        
        # Voice input button at the bottom of menu
        st.button("Start Voice Input", key="voice_btn", on_click=recognize_speech)
    
    with col2:
        st.markdown("""
        <h1 style='color: black; text-align: Top;'>Current Order</h1>""", unsafe_allow_html=True)
        
        if not st.session_state.current_order:
            st.markdown("<p style='color: black; '>Your order is empty. Add items from the menu or use voice commands.</p>", unsafe_allow_html = True)
        else:
            # Create a DataFrame for displaying the order with delete buttons
            order_items = []
            for i, item in enumerate(st.session_state.current_order):
                order_items.append({
                    "Coffee": item["coffee"],
                    "Quantity": item["quantity"],
                    "Remove": "🗑️"  # Bin emoji for delete action
                })
            
            order_df = pd.DataFrame(order_items)
            
            # Display each row with delete button
            for i, item in enumerate(order_items):
                cols = st.columns([3, 2, 1])  # Adjust column widths as needed
                
                cols[0].write(f"<p style='color: black; font-weight: bold;'>{item['Coffee']}</p>",unsafe_allow_html=True)
                cols[1].write(f"<p style='color: black;'>{item['Quantity']}</p>", unsafe_allow_html=True)
                
                # Delete button that reduces quantity by 1
                if cols[2].button("🗑️", key=f"remove_item_{i}"):
                    coffee = st.session_state.current_order[i]["coffee"]
                    if st.session_state.current_order[i]["quantity"] > 1:
                        # Reduce quantity by 1
                        st.session_state.current_order[i]["quantity"] -= 1
                        # Also update the coffee_quantities dictionary
                        st.session_state.coffee_quantities[coffee] -= 1
                        show_notification(f"➖ Reduced {coffee} quantity")
                    else:
                        # Remove the item if quantity becomes 0
                        st.session_state.coffee_quantities[coffee] = 0
                        st.session_state.current_order.pop(i)
                        show_notification(f"🗑️ Removed {coffee} from order")
                    st.session_state.should_rerun = True
            
            # Order buttons
            col_clear, col_complete = st.columns(2)
            
            with col_clear:
                if st.button("Clear Order", key="clear_btn"):
                    st.session_state.current_order = []
                    reset_quantities()
                    show_notification("🗑️ Order cleared")
                    st.session_state.should_rerun = True
            
            with col_complete:
                if st.button("Place Order", key="place_btn"):
                    complete_order()
                    
        st.markdown("""
        <h1 style='color: black; text-align: Top;'>Order History</h1>""", unsafe_allow_html=True)

        c.execute("SELECT id, items, timestamp FROM orders ORDER BY timestamp DESC LIMIT 10")
        orders = c.fetchall()
        
        if not orders:
            st.markdown("<p sytle='color: black;'>No previous orders found.</p>",unsafe_allow_html=True)
        else:
            for order in orders:
                order_id, items_json, timestamp = order
                with st.expander(f"Order #{order_id} - {timestamp}"):
                    try:
                        items = json.loads(items_json)
                        for item in items:
                            coffee = item.get("coffee", "Unknown Coffee")
                            quantity = item.get("quantity", 1)
                            st.markdown(f"<p style='color: black;'>**{quantity}x {coffee}**</p>",unsafe_allow_html=True)
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
        st.rerun()  # Keep this as experimental_rerun to maintain current behavior

if __name__ == "__main__":
    main()
