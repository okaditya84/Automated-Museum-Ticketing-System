# import os
# import json
# from flask import Flask, request, jsonify, session, render_template
# from groq import Groq
# from flask_session import Session
# import random

# app = Flask(__name__)

# # Configuration for session management
# app.config['SECRET_KEY'] = 'supersecretkey'
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)

# # Load API key from config.json
# working_dir = os.path.dirname(os.path.abspath(__file__))
# config_data = json.load(open(f"{working_dir}/config.json"))

# GROQ_API_KEY = config_data["GROQ_API_KEY"]
# os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# client = Groq()

# # Predefined FAQs for suggestions
# FAQS = [
#     "What are the museum's opening hours?",
#     "Are there any tickets available for this weekend?",
#     "What is the price of a family ticket?",
#     "Can I book a guided tour?"
# ]

# # Home route that renders a simple chat interface
# @app.route('/')
# def index():
#     if "chat_history" not in session:
#         session["chat_history"] = []
#     return render_template('index.html', chat_history=session["chat_history"], faqs=FAQS)

# # API endpoint for handling user prompt
# @app.route('/ask', methods=['POST'])
# def ask_llama():
#     user_prompt = request.json.get('prompt')

#     if not user_prompt:
#         return jsonify({"error": "No prompt provided"}), 400

#     # Add user message to chat history
#     session["chat_history"].append({"role": "user", "content": user_prompt})

#     # Prepare the message structure for the LLM
#     messages = [
#         {"role": "system", "content": "You are a helpful assistant for museum ticket booking. Answer questions about ticket availability, pricing, and events."},
#         *session["chat_history"]
#     ]

#     # Call the Groq API to get the response from the LLM
#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=messages
#     )
    
#     assistant_response = response.choices[0].message.content

#     # Add the assistant's response to chat history
#     session["chat_history"].append({"role": "assistant", "content": assistant_response})

#     return jsonify({"response": assistant_response})

# if __name__ == '__main__':
#     app.run(debug=True)



import os
import json
from flask import Flask, request, jsonify, session, render_template
from groq import Groq
from flask_session import Session
import random
import datetime

app = Flask(__name__)

# Configuration for session management
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Load API key from config.json
working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))

GROQ_API_KEY = config_data["GROQ_API_KEY"]
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

# Predefined events list
EVENTS = [
    {"name": "Ancient Egypt Exhibition", "date": "2024-10-15"},
    {"name": "Renaissance Art Workshop", "date": "2024-10-20"},
    {"name": "Modern Sculpture Tour", "date": "2024-10-25"},
    {"name": "Dinosaur Fossils Display", "date": "2024-11-01"},
]

# Home route that renders the chat interface
@app.route('/')
def index():
    # Reset chat history on each page load
    session["chat_history"] = []
    session["booking_state"] = None
    # Add initial greeting from AI
    ai_greeting = "Welcome to the Museum Chatbot! How can I assist you today? You can ask about tickets, events, or use the buttons below for quick actions."
    session["chat_history"].append({"role": "assistant", "content": ai_greeting})
    return render_template('index.html', chat_history=session["chat_history"], events=EVENTS)

# API endpoint for handling user prompt
@app.route('/ask', methods=['POST'])
def ask_llama():
    user_prompt = request.json.get('prompt')

    if not user_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Add user message to chat history
    session["chat_history"].append({"role": "user", "content": user_prompt})

    # Check if we're in the middle of a booking process
    if session.get("booking_state"):
        return handle_booking_process(user_prompt)

    # Prepare the message structure for the LLM
    messages = [
        {"role": "system", "content": "You are a helpful assistant for museum ticket booking. Provide concise and precise answers about ticket availability, pricing, and events. If the user wants to book a ticket, ask for name, age, contact, number of adults, and number of children in that order. Do not ask for all information at once, ask one by one."},
        *session["chat_history"]
    ]

    # Call the Groq API to get the response from the LLM
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    
    assistant_response = response.choices[0].message.content

    # Add the assistant's response to chat history
    session["chat_history"].append({"role": "assistant", "content": assistant_response})

    # Store the conversation in a text file using UTF-8 encoding
    with open('conversation_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"User: {user_prompt}\n")
        f.write(f"Assistant: {assistant_response}\n\n")

    return jsonify({"response": assistant_response})

def handle_booking_process(user_input):
    booking_state = session["booking_state"]
    booking_info = session.get("booking_info", {})

    if booking_state == "name":
        booking_info["name"] = user_input
        session["booking_state"] = "age"
        response = "Thank you. Could you please provide your age?"
    elif booking_state == "age":
        booking_info["age"] = int(user_input)
        session["booking_state"] = "contact"
        response = "Got it. What's your contact number?"
    elif booking_state == "contact":
        booking_info["contact"] = user_input
        session["booking_state"] = "adults"
        response = "Thank you. How many adult tickets do you need?"
    elif booking_state == "adults":
        booking_info["adults"] = int(user_input)
        session["booking_state"] = "children"
        response = "Understood. And how many children tickets (age under 10) do you need?"
    elif booking_state == "children":
        booking_info["children"] = int(user_input)
        session["booking_state"] = None
        
        # Calculate total price
        adult_price = 15
        child_price = 10
        senior_price = 10
        
        total_price = 0
        if booking_info["age"] >= 60:
            total_price += senior_price * booking_info["adults"]
        else:
            total_price += adult_price * booking_info["adults"]
        total_price += child_price * booking_info["children"]
        
        booking_info["total_price"] = total_price
        
        # Save booking info to a JSON file named after the user
        filename = f"{booking_info['name']}_booking.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(booking_info, f, ensure_ascii=False, indent=4)
        
        response = f"Great! Your booking is complete. Total price: ₹{total_price}. Your booking information has been saved."
    else:
        session["booking_state"] = "name"
        response = "Let's start the booking process. What's your name?"

    session["booking_info"] = booking_info
    session["chat_history"].append({"role": "assistant", "content": response})
    return jsonify({"response": response})

# API endpoint for initiating the booking process
@app.route('/start_booking', methods=['POST'])
def start_booking():
    session["booking_state"] = "name"
    response = "Let's start the booking process. What's your name?"
    session["chat_history"].append({"role": "assistant", "content": response})
    return jsonify({"response": response})

# API endpoint for fetching events
@app.route('/events', methods=['GET'])
def get_events():
    return jsonify(EVENTS)

if __name__ == '__main__':
    app.run(debug=True)