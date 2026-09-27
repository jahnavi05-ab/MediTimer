# 💊 MediTimer – Smart Medicine Reminder Application

MediTimer is a Python-based desktop medicine reminder application designed to help users manage their medication schedules efficiently.

The application allows users to create medicine reminders by entering the medicine name, dosage, reminder time, user type, and duration. It provides timely notifications and includes voice assistance for elderly users.

---

## 🚀 Features

- 👤 User-based medicine reminder management
- 💊 Add medicine name and dosage
- ⏰ Schedule medicine reminders using `HH:MM` format
- 🔔 Desktop notifications for scheduled medicines
- 🗣️ Voice assistance for elderly users
- 👴 Separate support for Elder and Normal user types
- 📅 Medicine duration management
- 💾 JSON-based local data storage
- 🖥️ User-friendly desktop graphical interface
- ⏱️ Automatic reminder scheduling
- 🎨 Clean and simple GUI

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python** | Core programming language |
| **Tkinter / ttk** | Desktop graphical user interface |
| **ttkbootstrap** | Modern GUI styling |
| **JSON** | Local data storage |
| **pyttsx3** | Text-to-speech / voice assistance |
| **Plyer** | Desktop notifications |

---

## 🏗️ Project Structure

```text
MediTimer/
│
├── app.py
├── users.json
├── reminders.json
└── README.md