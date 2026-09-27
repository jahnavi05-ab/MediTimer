# 💊 MediTimer – Smart Medicine Reminder App

MediTimer is a Python-based desktop medicine reminder application built with Tkinter. It helps users manage medicine schedules and receive timely reminders.

The application supports user login and signup, medicine reminder management, desktop notifications, and spoken reminders for elderly users.

---

## 🚀 Features

- 👤 User signup and login
- 🔐 Password hashing using SHA-256
- 💊 Add medicine name and dosage
- ⏰ Schedule medicine reminders using 24-hour time format
- 🔔 Desktop notifications for scheduled medicines
- 🗣️ Spoken reminders for elderly users
- 👵 Elder profile with spoken and visual reminders
- 🙂 Normal profile with visual reminders
- 📋 View scheduled medicine reminders
- 🗑️ Delete scheduled reminders
- 💾 Local JSON-based data storage
- 🖥️ Modern desktop graphical user interface
- 🔄 Automatic daily reminder scheduling

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python** | Core programming language |
| **Tkinter / ttk** | Desktop graphical user interface |
| **ttkbootstrap** | GUI styling and customization |
| **JSON** | Local data storage |
| **pyttsx3** | Text-to-speech / voice reminders |
| **Plyer** | Desktop notifications |
| **Schedule** | Daily reminder scheduling |
| **hashlib** | Password hashing |

---

## 📂 Project Structure

```text
MediTimer/
│
├── app.py
├── users.json
├── reminders.json
└── README.md