"""
MediTimer — Medicine Reminder App
A desktop reminder app built with Tkinter that helps users (especially elders)
never miss a dose. Supports login/signup, spoken reminders for elders,
desktop notifications, and a clean modern UI.
"""

import json
import os
import time
import uuid
import hashlib
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from plyer import notification
except ImportError:
    notification = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

import schedule

# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------
USERS_FILE = "users.json"
REMINDERS_FILE = "reminders.json"


def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


users = load_json(USERS_FILE)
reminders = load_json(REMINDERS_FILE)

# --------------------------------------------------------------------------
# Design system — colors, fonts, spacing
# --------------------------------------------------------------------------
COLORS = {
    "bg": "#F3F4FB",
    "surface": "#FFFFFF",
    "primary": "#5B5BF7",
    "primary_dark": "#4646D8",
    "secondary": "#22C1A0",
    "secondary_dark": "#1AA88B",
    "danger": "#EF5A6F",
    "danger_dark": "#D8455A",
    "text": "#1F2233",
    "muted": "#7A7F9A",
    "border": "#E4E6F5",
    "elder_badge": "#FFA94D",
    "normal_badge": "#5B5BF7",
}

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Helvetica"
FONTS = {
    "title": (FONT_FAMILY, 26, "bold"),
    "subtitle": (FONT_FAMILY, 12),
    "heading": (FONT_FAMILY, 16, "bold"),
    "label": (FONT_FAMILY, 10, "bold"),
    "body": (FONT_FAMILY, 11),
    "small": (FONT_FAMILY, 9),
    "button": (FONT_FAMILY, 11, "bold"),
}


# --------------------------------------------------------------------------
# Reusable widgets
# --------------------------------------------------------------------------
class RoundedButton(tk.Canvas):
    """A flat, rounded, hover-aware button drawn on a canvas."""

    def __init__(self, parent, text, command=None, width=200, height=42,
                 radius=14, bg=COLORS["primary"], hover=COLORS["primary_dark"],
                 fg="white", font=FONTS["button"]):
        super().__init__(parent, width=width, height=height,
                          bg=parent["bg"] if isinstance(parent["bg"], str) else COLORS["bg"],
                          highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self.bg_color = bg
        self.hover_color = hover
        self.radius = radius
        self.width = width
        self.height = height
        self._draw(bg, text, fg, font)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self._draw(self.hover_color, text, fg, font))
        self.bind("<Leave>", lambda e: self._draw(self.bg_color, text, fg, font))

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r,
                  x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
                  x1, y1 + r, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, color, text, fg, font):
        self.delete("all")
        self._round_rect(2, 2, self.width - 2, self.height - 2, self.radius, fill=color, outline=color)
        self.create_text(self.width / 2, self.height / 2, text=text, fill=fg, font=font)

    def _on_click(self, event):
        if self.command:
            self.command()


def make_card(parent, padx=30, pady=25, **grid_or_pack):
    """A white 'card' surface with a subtle border, used as a content container."""
    outer = tk.Frame(parent, bg=COLORS["border"], bd=0)
    inner = tk.Frame(outer, bg=COLORS["surface"], padx=padx, pady=pady)
    inner.pack(padx=1, pady=1, fill="both", expand=True)
    return outer, inner


def styled_entry(parent, placeholder="", show=None, width=28):
    """An Entry with placeholder-style behaviour and a bottom border look."""
    wrapper = tk.Frame(parent, bg=COLORS["surface"])
    entry = tk.Entry(wrapper, font=FONTS["body"], relief="flat", bg="#F7F8FD",
                      fg=COLORS["text"], insertbackground=COLORS["text"], width=width)
    entry.pack(ipady=8, ipadx=8, fill="x")
    underline = tk.Frame(wrapper, bg=COLORS["border"], height=2)
    underline.pack(fill="x")

    entry._placeholder = placeholder
    entry._is_placeholder = False
    entry._show_char = show

    def set_placeholder():
        entry.delete(0, tk.END)
        entry.insert(0, placeholder)
        entry.config(fg=COLORS["muted"])
        if show:
            entry.config(show="")
        entry._is_placeholder = True

    def clear_placeholder(event=None):
        if entry._is_placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=COLORS["text"])
            if show:
                entry.config(show=show)
            entry._is_placeholder = False

    def restore_placeholder(event=None):
        if not entry.get():
            set_placeholder()

    entry.bind("<FocusIn>", clear_placeholder)
    entry.bind("<FocusOut>", restore_placeholder)
    set_placeholder()

    def get_value():
        return "" if entry._is_placeholder else entry.get().strip()

    entry.get_value = get_value
    wrapper.entry = entry
    return wrapper


def field_label(parent, text):
    tk.Label(parent, text=text, font=FONTS["label"], bg=COLORS["surface"],
             fg=COLORS["muted"]).pack(anchor="w", pady=(12, 4))


def center_window(win, width, height):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw - width) // 2, (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


# --------------------------------------------------------------------------
# Reminder engine
# --------------------------------------------------------------------------
def speak(text):
    if pyttsx3 is None:
        return
    try:
        local_engine = pyttsx3.init()
        local_engine.say(text)
        local_engine.runAndWait()
        local_engine.stop()
    except Exception as e:
        print(f"[voice] could not speak reminder: {e}")


def reminder_popup(name, dosage, user_type):
    """Fires when a scheduled reminder is due: notification + optional voice."""
    if notification is not None:
        try:
            notification.notify(
                title="💊 Medicine Reminder",
                message=f"Time to take {name} ({dosage})",
                timeout=10,
            )
        except Exception as e:
            print(f"[notification] failed: {e}")
    if user_type == "Elder":
        threading.Thread(
            target=speak,
            args=(f"Please take your medicine {name}, dosage {dosage}",),
            daemon=True,
        ).start()


def background_reminder_check():
    while True:
        schedule.run_pending()
        time.sleep(5)


def schedule_reminder(reminder_id, time_str, name, dosage, user_type):
    schedule.every().day.at(time_str).do(
        reminder_popup, name, dosage, user_type
    ).tag(reminder_id)


def unschedule_reminder(reminder_id):
    schedule.clear(reminder_id)


# Load any reminders saved from a previous run
for _uname, _rems in reminders.items():
    for _r in _rems:
        try:
            datetime.strptime(_r["time"], "%H:%M")
            schedule_reminder(_r["id"], _r["time"], _r["name"], _r["dosage"], _r["type"])
        except Exception as e:
            print(f"Skipped invalid reminder for {_r.get('name')}: {e}")

threading.Thread(target=background_reminder_check, daemon=True).start()


# --------------------------------------------------------------------------
# Main application
# --------------------------------------------------------------------------
class MediApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MediTimer — Medicine Reminder")
        self.root.configure(bg=COLORS["bg"])
        center_window(self.root, 760, 560)
        self.root.minsize(720, 540)

        self.user = None
        self.user_type = None

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", font=FONTS["body"], padding=(18, 10))
        self.style.configure("Treeview", font=FONTS["body"], rowheight=32,
                              background=COLORS["surface"], fieldbackground=COLORS["surface"])
        self.style.configure("Treeview.Heading", font=FONTS["label"])
        self.style.configure("TCombobox", font=FONTS["body"])

        self.create_home()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def container(self):
        wrap = tk.Frame(self.root, bg=COLORS["bg"])
        wrap.pack(fill="both", expand=True)
        return wrap

    # ---------------- Home ----------------
    def create_home(self):
        self.clear()
        wrap = self.container()

        center = tk.Frame(wrap, bg=COLORS["bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="💊", font=(FONT_FAMILY, 46), bg=COLORS["bg"]).pack()
        tk.Label(center, text="MediTimer", font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=(0, 4))
        tk.Label(center, text="Never miss a dose again.", font=FONTS["subtitle"],
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=(0, 30))

        RoundedButton(center, "Log In", command=self.login_screen,
                      bg=COLORS["primary"], hover=COLORS["primary_dark"],
                      width=240, height=46).pack(pady=8)
        RoundedButton(center, "Create Account", command=self.signup_screen,
                      bg=COLORS["secondary"], hover=COLORS["secondary_dark"],
                      width=240, height=46).pack(pady=8)

    # ---------------- Login ----------------
    def login_screen(self):
        self.clear()
        wrap = self.container()
        outer, card = make_card(wrap)
        outer.place(relx=0.5, rely=0.5, anchor="center", width=380)

        tk.Label(card, text="Welcome back", font=FONTS["heading"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(card, text="Log in to manage your reminders", font=FONTS["small"],
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 10))

        field_label(card, "USERNAME")
        u_field = styled_entry(card, "e.g. asha_92")
        u_field.pack(fill="x")

        field_label(card, "PASSWORD")
        p_field = styled_entry(card, "••••••••", show="*")
        p_field.pack(fill="x")

        error_lbl = tk.Label(card, text="", font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["danger"])
        error_lbl.pack(anchor="w", pady=(6, 0))

        def do_login():
            uname, pwd = u_field.entry.get_value(), p_field.entry.get_value()
            if not uname or not pwd:
                error_lbl.config(text="Please fill in both fields.")
                return
            if uname in users and users[uname] == hash_password(pwd):
                self.user = uname
                self.ask_user_type()
            else:
                error_lbl.config(text="Invalid username or password.")

        btn_row = tk.Frame(card, bg=COLORS["surface"])
        btn_row.pack(fill="x", pady=(18, 0))
        RoundedButton(btn_row, "Log In", command=do_login, width=310, height=44).pack()

        back_lbl = tk.Label(card, text="← Back", font=FONTS["small"], bg=COLORS["surface"],
                             fg=COLORS["muted"], cursor="hand2")
        back_lbl.pack(anchor="w", pady=(14, 0))
        back_lbl.bind("<Button-1>", lambda e: self.create_home())

        self.root.bind("<Return>", lambda e: do_login())

    # ---------------- Signup ----------------
    def signup_screen(self):
        self.clear()
        self.root.unbind("<Return>")
        wrap = self.container()
        outer, card = make_card(wrap)
        outer.place(relx=0.5, rely=0.5, anchor="center", width=380)

        tk.Label(card, text="Create your account", font=FONTS["heading"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(card, text="Takes less than a minute", font=FONTS["small"],
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 10))

        field_label(card, "USERNAME")
        u_field = styled_entry(card, "Choose a username")
        u_field.pack(fill="x")

        field_label(card, "PASSWORD")
        p_field = styled_entry(card, "At least 4 characters", show="*")
        p_field.pack(fill="x")

        field_label(card, "CONFIRM PASSWORD")
        p2_field = styled_entry(card, "Re-enter password", show="*")
        p2_field.pack(fill="x")

        error_lbl = tk.Label(card, text="", font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["danger"])
        error_lbl.pack(anchor="w", pady=(6, 0))

        def register():
            uname = u_field.entry.get_value()
            pwd = p_field.entry.get_value()
            pwd2 = p2_field.entry.get_value()
            if not uname or not pwd:
                error_lbl.config(text="Username and password are required.")
                return
            if len(pwd) < 4:
                error_lbl.config(text="Password must be at least 4 characters.")
                return
            if pwd != pwd2:
                error_lbl.config(text="Passwords do not match.")
                return
            if uname in users:
                error_lbl.config(text="That username is already taken.")
                return
            users[uname] = hash_password(pwd)
            save_json(USERS_FILE, users)
            messagebox.showinfo("Welcome!", "Account created successfully. Please log in.")
            self.login_screen()

        btn_row = tk.Frame(card, bg=COLORS["surface"])
        btn_row.pack(fill="x", pady=(18, 0))
        RoundedButton(btn_row, "Create Account", command=register,
                      bg=COLORS["secondary"], hover=COLORS["secondary_dark"],
                      width=310, height=44).pack()

        back_lbl = tk.Label(card, text="← Back", font=FONTS["small"], bg=COLORS["surface"],
                             fg=COLORS["muted"], cursor="hand2")
        back_lbl.pack(anchor="w", pady=(14, 0))
        back_lbl.bind("<Button-1>", lambda e: self.create_home())

    # ---------------- Choose user type ----------------
    def ask_user_type(self):
        self.clear()
        self.root.unbind("<Return>")
        wrap = self.container()
        center = tk.Frame(wrap, bg=COLORS["bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text=f"Hi {self.user} 👋", font=FONTS["heading"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(0, 4))
        tk.Label(center, text="Who is this profile for?", font=FONTS["subtitle"],
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=(0, 24))

        row = tk.Frame(center, bg=COLORS["bg"])
        row.pack()

        for label, sub, color, hover, utype in [
            ("👵 Elder", "Spoken + visual reminders", COLORS["elder_badge"], "#E6923D", "Elder"),
            ("🙂 Normal", "Visual reminders only", COLORS["normal_badge"], COLORS["primary_dark"], "Normal"),
        ]:
            outer, card = make_card(row, padx=24, pady=20)
            outer.pack(side="left", padx=10)
            tk.Label(card, text=label, font=FONTS["heading"], bg=COLORS["surface"]).pack()
            tk.Label(card, text=sub, font=FONTS["small"], bg=COLORS["surface"],
                     fg=COLORS["muted"]).pack(pady=(2, 14))
            RoundedButton(card, "Choose", command=lambda t=utype: self.start_dashboard(t),
                          bg=color, hover=hover, width=160, height=38).pack()

    # ---------------- Dashboard ----------------
    def start_dashboard(self, utype):
        self.user_type = utype
        self.clear()
        wrap = self.container()

        # Header
        header = tk.Frame(wrap, bg=COLORS["primary"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        badge_color = COLORS["elder_badge"] if utype == "Elder" else "#8C8CFA"
        tk.Label(header, text=f"💊 MediTimer", font=FONTS["heading"], bg=COLORS["primary"],
                 fg="white").pack(side="left", padx=20)
        tk.Label(header, text=f"{self.user} · {utype} profile", font=FONTS["small"],
                 bg=badge_color, fg="white", padx=10, pady=4).pack(side="left")

        logout_canvas = RoundedButton(header, "Logout", command=self.logout,
                                       bg="#4646D8", hover="#3838B8", width=100, height=32,
                                       radius=10)
        logout_canvas.pack(side="right", padx=20)

        # Body: notebook with two tabs
        body = tk.Frame(wrap, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=20)

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)

        add_tab = tk.Frame(notebook, bg=COLORS["bg"])
        list_tab = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(add_tab, text="  ➕ Add Reminder  ")
        notebook.add(list_tab, text="  📋 My Reminders  ")

        self.build_add_tab(add_tab)
        self.build_list_tab(list_tab)

    def build_add_tab(self, parent):
        outer, card = make_card(parent, padx=30, pady=25)
        outer.pack(fill="x", pady=10)

        tk.Label(card, text="New reminder", font=FONTS["heading"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w")

        row1 = tk.Frame(card, bg=COLORS["surface"])
        row1.pack(fill="x", pady=(10, 0))

        col1 = tk.Frame(row1, bg=COLORS["surface"])
        col1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        field_label(col1, "MEDICINE NAME")
        name_field = styled_entry(col1, "e.g. Paracetamol")
        name_field.pack(fill="x")

        col2 = tk.Frame(row1, bg=COLORS["surface"])
        col2.pack(side="left", fill="x", expand=True)
        field_label(col2, "DOSAGE")
        dose_field = styled_entry(col2, "e.g. 500mg, 1 tablet")
        dose_field.pack(fill="x")

        field_label(card, "REMINDER TIME (24-hour)")
        time_row = tk.Frame(card, bg=COLORS["surface"])
        time_row.pack(anchor="w", pady=(0, 4))

        hour_var = tk.StringVar(value="08")
        min_var = tk.StringVar(value="00")
        hour_box = ttk.Combobox(time_row, textvariable=hour_var, width=4, state="readonly",
                                 values=[f"{h:02d}" for h in range(24)])
        hour_box.pack(side="left")
        tk.Label(time_row, text=":", font=FONTS["heading"], bg=COLORS["surface"]).pack(side="left", padx=4)
        min_box = ttk.Combobox(time_row, textvariable=min_var, width=4, state="readonly",
                                values=[f"{m:02d}" for m in range(0, 60, 5)])
        min_box.pack(side="left")

        status_lbl = tk.Label(card, text="", font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["danger"])
        status_lbl.pack(anchor="w", pady=(8, 0))

        def add_reminder():
            med = name_field.entry.get_value()
            dose = dose_field.entry.get_value()
            tm = f"{hour_var.get()}:{min_var.get()}"

            if not med or not dose:
                status_lbl.config(text="Please enter both a medicine name and dosage.", fg=COLORS["danger"])
                return

            reminder_id = str(uuid.uuid4())[:8]
            entry = {"id": reminder_id, "name": med, "dosage": dose, "time": tm, "type": self.user_type}
            reminders.setdefault(self.user, []).append(entry)
            save_json(REMINDERS_FILE, reminders)
            schedule_reminder(reminder_id, tm, med, dose, self.user_type)

            status_lbl.config(text=f"✓ Reminder for {med} set at {tm}.", fg=COLORS["secondary_dark"])
            for field in (name_field, dose_field):
                field.entry.delete(0, tk.END)
                field.entry._is_placeholder = False
                field.entry.event_generate("<FocusOut>")  # restores the placeholder text
            card.focus_set()
            self.refresh_reminder_list()

        RoundedButton(card, "Save Reminder", command=add_reminder,
                      bg=COLORS["secondary"], hover=COLORS["secondary_dark"],
                      width=200, height=42).pack(anchor="w", pady=(14, 0))

    def build_list_tab(self, parent):
        outer, card = make_card(parent, padx=20, pady=20)
        outer.pack(fill="both", expand=True, pady=10)

        tk.Label(card, text="Your scheduled reminders", font=FONTS["heading"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        columns = ("time", "name", "dosage")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", height=10)
        self.tree.heading("time", text="Time")
        self.tree.heading("name", text="Medicine")
        self.tree.heading("dosage", text="Dosage")
        self.tree.column("time", width=80, anchor="center")
        self.tree.column("name", width=220)
        self.tree.column("dosage", width=160)
        self.tree.pack(fill="both", expand=True)

        btn_row = tk.Frame(card, bg=COLORS["surface"])
        btn_row.pack(anchor="e", pady=(10, 0))
        RoundedButton(btn_row, "Delete Selected", command=self.delete_selected_reminder,
                      bg=COLORS["danger"], hover=COLORS["danger_dark"],
                      width=170, height=38, radius=10).pack()

        self.refresh_reminder_list()

    def refresh_reminder_list(self):
        if not hasattr(self, "tree"):
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in sorted(reminders.get(self.user, []), key=lambda x: x["time"]):
            self.tree.insert("", "end", iid=r["id"], values=(r["time"], r["name"], r["dosage"]))

    def delete_selected_reminder(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select a reminder", "Please select a reminder to delete.")
            return
        reminder_id = selected[0]
        user_reminders = reminders.get(self.user, [])
        reminders[self.user] = [r for r in user_reminders if r["id"] != reminder_id]
        save_json(REMINDERS_FILE, reminders)
        unschedule_reminder(reminder_id)
        self.refresh_reminder_list()

    def logout(self):
        self.user = None
        self.user_type = None
        self.create_home()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MediApp(root)
    root.mainloop()
