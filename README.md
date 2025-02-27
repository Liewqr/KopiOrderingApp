# KopiOrderingApp

A voice-controlled Streamlit application that allows users to order coffee through both voice commands and a graphical interface. This app provides an intuitive way to place coffee orders with customizable add-ons.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
  - [Virtual Environment Setup](#virtual-environment-setup)
- [Usage](#usage)
  - [Voice Commands](#voice-commands)
  - [UI Interaction](#ui-interaction)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Overview

KopiOrderingApp solves the problem of streamlining coffee ordering processes in cafes or for personal use. It provides both voice and UI-based interactions, making it accessible for various user preferences. The target audience includes coffee shops looking to modernize their ordering systems and developers interested in speech recognition applications.

## Features

- **Voice Recognition Ordering:** Order coffee using natural speech commands.
- **Interactive Menu Interface:** Browse and select from a variety of coffee options and add-ons.
- **Order Management:** Add, remove, and modify items in your current order.
- **Text-to-Speech Feedback:** Receive audible confirmation of your actions.
- **Order History:** All completed orders are saved to a database for future reference.

## Tech Stack

- **Programming Languages:** Python
- **Frameworks/Libraries:**
  - Streamlit - Web application framework
  - SpeechRecognition - Voice command processing
  - pyttsx3 - Text-to-speech functionality
  - Threading - Concurrent processing
- **Databases:** SQLite (coffee_orders.db)

## Installation & Setup

### Clone the Repository

```bash
git clone https://github.com/yourusername/KopiOrderingApp.git
cd KopiOrderingApp
```

### Virtual Environment Setup

It is highly recommended to use a virtual environment to manage your project's dependencies.

**For macOS and Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**For Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

Once activated, your terminal prompt will indicate that you're working within the virtual environment.

To deactivate the virtual environment at any time, simply run:

```bash
deactivate
```

### Install Dependencies

After activating your virtual environment, install the required packages:

```bash
pip install -r requirements.txt
```

### Run the Application

Start the app using Streamlit:

```bash
streamlit run app.py
```

## Usage

### Voice Commands

- **Add Items:** Say a coffee name (e.g., "I'd like a Latte") to add it to your order.
- **Customize Order:** Include add-ons in your speech (e.g., "Cappuccino with Vanilla Syrup").
- **Finalize Order:** Say "complete order" to finalize your current order.
- **Reset Order:** Say "clear order" to reset your selections.

### UI Interaction

- **Browse Menu:** Use the interactive menu to select desired add-ons.
- **Add Items:** Click "Add [Coffee]" buttons to add items to your order.
- **Review Order:** Your current order is visible in the sidebar.
- **Modify Order:** Use "Remove" buttons to edit your selections.
- **Complete Order:** Click "Complete Order" to finalize or "Clear Order" to start over.

## Configuration

The application requires the following Python packages:

- streamlit
- sqlite3
- speech_recognition
- pyttsx3

For voice recognition functionality, ensure your system has a working microphone and appropriate audio drivers installed.

## Contributing

No specific contribution guidelines provided.

## License

MIT License

KopiOrderingApp demonstrates the integration of voice recognition technology with a practical everyday use case. The combination of speech recognition and a user-friendly interface makes coffee ordering accessible to everyone.

---
