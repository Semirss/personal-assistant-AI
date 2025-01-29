import csv
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import pyttsx3
import speech_recognition as sr
from plyer import notification
from datetime import datetime ,timedelta
from dateutil import parser
import time
import json
import os
import re
import pygame
import random


# File paths for storing data
notes_file = "notes.json"
contacts_file = "contacts.json"
events_file = "events.json"
reminders_file = "reminders.json"
birthdays_file = "birthdays.json"

# Load dataset
def load_dataset(file_path):
    data = []
    with open(file_path, mode="r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            # Combine the category and details as the label
            category = row[0]  # Category
            item = row[1]  # Item
            details = row[2]  # Details
            label = category  # Use category as the label
            text = f"{item} {details}"  # Combine item and details as input text
            data.append((text, label))
    return data
def append_to_dataset(text, category):
    # Open the dataset in append mode
    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([category, text, "User added data"])  # Add text and its category
    print(f"Appended to dataset: {text} -> {category}")

# File path to your dataset
file_path = "assistant_dataset_500_extended.csv"  # Ensure this matches your local file path

# Load and preprocess the dataset
data = load_dataset(file_path)
vectorizer = CountVectorizer()
X = vectorizer.fit_transform([d[0] for d in data])  # Text data
y = np.array([d[1] for d in data])  # Labels

# Train the model
model = MultinomialNB()
model.fit(X, y)

# Recognize speech using the microphone
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
        except sr.RequestError:
            print("Sorry, my speech service is down.")
            
def preprocess_text(text):
    text = text.lower().strip()  # Convert to lowercase and remove extra spaces
    return text

# Use the model to make a prediction
def predict_command(text):
    text = preprocess_text(text)
    X_new = vectorizer.transform([text])
    prediction = model.predict(X_new)[0]  # Predicted category
    print(f"Predicted Category: {prediction}")
    
    # Append the user's request to the dataset
    append_to_dataset(text, prediction)

    return prediction
def retrain_model():
    global model, vectorizer
    data = load_dataset(file_path)
    X = vectorizer.fit_transform([d[0] for d in data])  # Text data
    y = np.array([d[1] for d in data])  # Labels
    model.fit(X, y)
    

   

# Convert text to speech
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Load data from JSON files
def load_json(file_name, default_value):
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            return json.load(file)
    else:
        return default_value

# Save data to JSON files
def save_json(file_name, data):
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)

# List of reminders and birthdays (you can modify this list)
reminders = load_json(reminders_file, [])
birthdays = load_json(birthdays_file, [])

# Note, Event, and Contact storage
notes = load_json(notes_file, [])
events = load_json(events_file, [])
contacts = load_json(contacts_file, {})

# Function to check and notify reminders
def check_reminders():
    current_time = datetime.now()
    for reminder in reminders:
        reminder_time = datetime.strptime(reminder["time"], "%Y-%m-%d %H:%M")
        if current_time >= reminder_time and not reminder.get("notified", False):
            # Speak the reminder
            speak(f"Reminder: {reminder['text']}")
            # Print to terminal for notification
            print(f"[REMINDER] {reminder['text']} at {reminder_time}")
            # Show desktop notification
            notification.notify(
                title="Reminder",
                message=reminder["text"],
                timeout=10  # Notification duration in seconds
            )
            reminder["notified"] = True  # Mark as notified

# Function to check and notify birthdays
def check_birthdays():
    current_date = datetime.now().date()
    for birthday in birthdays:
        birth_date = datetime.strptime(birthday["birthdate"], "%Y-%m-%d").date()
        if current_date == birth_date:
            # Speak the birthday message
            speak(f"Today is {birthday['name']}'s birthday!")
            # Print to terminal for notification
            print(f"[BIRTHDAY] Today is {birthday['name']}'s birthday!")
            # Show desktop notification
            notification.notify(
                title="Birthday Reminder",
                message=f"Today is {birthday['name']}'s birthday!",
                timeout=10  # Notification duration in seconds
            )

# Function to handle reminders




def set_reminder():
    while True:  # Loop to keep asking until the user says "go out"
        speak("What would you like your reminder to say?")
        reminder_text = recognize_speech()
        
        if reminder_text:
            speak("When would you like to be reminded? Please say the date and time.")
            reminder_time = recognize_speech()
            
            if reminder_time:
                try:
                    # Check if the user said something like "after X minutes"
                    relative_time_match = re.search(r'(\d+)\s*(minute|hour|day)s?\s*(after|in)', reminder_time.lower())
                    if relative_time_match:
                        # Parse the number and the unit (minute/hour/day)
                        amount = int(relative_time_match.group(1))
                        unit = relative_time_match.group(2)
                        
                        # Calculate the future time
                        now = datetime.now()
                        if unit == "minute":
                            reminder_date_time = now + timedelta(minutes=amount)
                        elif unit == "hour":
                            reminder_date_time = now + timedelta(hours=amount)
                        elif unit == "day":
                            reminder_date_time = now + timedelta(days=amount)
                    else:
                        # Parse an absolute date and time if no relative time is mentioned
                        reminder_date_time = parser.parse(reminder_time)
                    
                    # Format the date and time to the required format
                    reminder_date_time_str = reminder_date_time.strftime("%Y-%m-%d %H:%M")
                    
                    reminders.append({"text": reminder_text, "time": reminder_date_time_str, "notified": False})
                    save_json(reminders_file, reminders)  # Save to JSON file
                    speak(f"Reminder saved: {reminder_text} at {reminder_date_time_str}")
                    print(f"Reminder saved: {reminder_text} at {reminder_date_time_str}")
                    return  # Exit the loop and return to the outer listening part
                
                except ValueError:
                    speak("Sorry, I couldn't understand the date and time format.")
                    print("Invalid date and time format.")
            else:
                speak("I didn't catch the time. Please try again.")
        
        else:
            speak("I didn't catch the reminder text. Please try again.")
        
        # Check if the user wants to go out
        speak("Do you want to go out? Say 'go out' to exit.")
        go_out_response = recognize_speech()
        if go_out_response and "go out" in go_out_response.lower():
            speak("Exiting now.")
            print("Exiting...")
            break  # Exit the loop and return to the outer listening part




# Initialize the pygame mixer
pygame.mixer.init()

# List of your music files (provide the correct paths to your MP3 files)
music_files = [
    r"D:/ai assigment/Heartbreaking(chosic.com).mp3",
    r"D:/ai assigment/Morning-Routine-Lofi-Study-Music(chosic.com).mp3",
    r"D:/ai assigment/Wildflowers-chosic.com_.mp3",  # Add more files as needed
]

def play_music():
    # Randomly choose a music file from the list
    chosen_music = random.choice(music_files)
    
    # Check if the file exists
    if os.path.exists(chosen_music):
        pygame.mixer.music.load(chosen_music)
        pygame.mixer.music.play(-1)  # Play the music looped indefinitely
        speak("Now playing music.")  # Optional: announce the action
        print(f"Now playing: {chosen_music}")
    else:
        speak("Sorry, I couldn't find the music file.")  # Optional: notify if the file is missing
        print("Music file not found.")

def stop_music():
    # Stop the music
    pygame.mixer.music.stop()
    speak("Music stopped.")  # Optional: announce the action
    print("Music stopped.")

# Example of how you can call it (depending on your voice command recognition)
def handle_command(command):
    if "music" in command.lower():
        play_music()
    elif "stop music" in command.lower():
        stop_music()

# Function to handle notes
def take_note():
    while True:  # Loop to keep asking until the user says "go out"
        speak("Please say the note you want to save.")
        note = recognize_speech()
        
        if note:
            notes.append(note)
            save_json(notes_file, notes)  # Save to JSON file
            speak(f"Note saved: {note}")
            print(f"Note saved: {note}")
            return  # Exit the loop and return to the outer listening part
        
        else:
            speak("I didn't catch the note. Please try again.")
        
        # Check if the user wants to go out
        speak("If you want to more assistance? Say 'go out' to exit.")
        go_out_response = recognize_speech()
        if go_out_response and "go out" in go_out_response.lower():
            speak("Exiting now.")
            print("Exiting...")
            break  # Exit the loop and return to the outer listening part

# Function to handle events
def add_event():
    speak("Please provide the event details.")
    event_details = recognize_speech()
    if event_details:
        speak("Please provide the event date .")
        event_time = recognize_speech()
        if event_time:
            try:
                event_date_time = datetime.strptime(event_time, "%m-%d %H:%M")
                events.append({"details": event_details, "time": event_date_time})
                save_json(events_file, events)  # Save to JSON file
                speak(f"Event saved: {event_details} at {event_date_time}")
                print(f"Event saved: {event_details} at {event_date_time}")
            except ValueError:
                speak("Sorry, I couldn't understand the date and time format.")
                print("Invalid date and time format.")
 # search contact  
              
def search_contact():
    speak("Please say the name of the contact you want to search for.")
    contact_name = recognize_speech()  # Get the name from the user
    if contact_name:
        contact_name = contact_name.lower()  # Normalize the input for case-insensitivity
        if contact_name in contacts:
            contact_number = contacts[contact_name]
            speak(f"The phone number for {contact_name} is {contact_number}.")
            print(f"Contact found: {contact_name} - {contact_number}")
        else:
            speak(f"Sorry, I couldn't find a contact named {contact_name}.")
            print(f"Contact {contact_name} not found.")
# Function to handle contacts
def add_contact():
    while True:  # Loop to keep asking until the user says "go out"
        speak("Please say the contact name.")
        contact_name = recognize_speech()
        
        if contact_name:
            speak(f"Please provide the contact's phone number for {contact_name}.")
            contact_number = recognize_speech()
            
            if contact_number:
                contacts[contact_name] = contact_number
                save_json(contacts_file, contacts)  # Save to JSON file
                speak(f"Contact saved: {contact_name} - {contact_number}")
                print(f"Contact saved: {contact_name} - {contact_number}")
                return  # Exit the loop and return to the outer listening part
            
        else:
            speak("I didn't catch the name. Please try again.")
        
        # Check if the user wants to go out
        speak("Do you want to go out? Say 'go out' to exit.")
        go_out_response = recognize_speech()
        if go_out_response and "go out" in go_out_response.lower():
            speak("Exiting now.")
            print("Exiting...")
            break  # Exit the loop and return to the outer listening part

# Function to show saved notes
def show_notes():
    if notes:
        note_list = "\n".join(notes)
        speak(f"Here are your notes: {note_list}")
        print(f"Here are your notes:\n{note_list}")
    else:
        speak("No notes saved.")
        print("No notes saved.")

# Function to show saved contacts
def show_contacts():
    if contacts:
        contact_list = "\n".join([f"{name}: {number}" for name, number in contacts.items()])
        speak(f"Here are your contacts: {contact_list}")
        print(f"Here are your contacts:\n{contact_list}")
    else:
        speak("No contacts saved.")
        print("No contacts saved.")

# Main function to integrate all components
# Main function to integrate all components
def main():
    while True:
        
        check_reminders()
        # Recognize speech and predict command
        command = recognize_speech()
        if command:
            
            if "close ai" in command.lower():
                speak("Goodbye sir!")
                print("Assistant closing...")
                print("Assistant closed...")
                break

            # Predict the command category
            response = predict_command(command)
            speak(f"Category detected: {response}")
            retrain_model()
            # Handle commands based on their category
            if response == "Task":
                speak("Let me assist you with a task.")
            elif response == "Reminder":
                set_reminder()
            elif response == "Contact":
                add_contact()
            elif response == "Note":
                take_note()
            elif response == "Event":
                speak("I am sorry this feature is not available for now")
            elif response == "Birthday":
                speak("I am sorry this feature is not available for now?")
               
            elif response == "Music":
                play_music()
            elif response == "Stop":
                stop_music()
            elif response == "Expense":
                speak("I am sorry this feature is not available for now")
           
            else:
                speak("I'm sorry, I didn't understand that command.")

        
        time.sleep(1)  

# Run the assistant
if __name__ == "__main__":
    main()
