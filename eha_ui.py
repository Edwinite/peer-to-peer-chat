"""
Tkinter UI for the P2P chat.

Notes on macOS compatibility:

* All Tk objects are created on the main thread inside `__init__`. Background
  services (announcer, discovery, responder) run on daemon threads and
  schedule UI updates via `self.master.after(...)` — the only thread-safe
  way to touch Tk widgets from another thread.

* The original implementation had a second polling thread that opened a new
  TCP connection to every known peer once per second to pull messages. That
  approach was incorrect (the responder never sends anything on that socket,
  so the recv would hang until the 10-second timeout), flooded the network,
  and on macOS triggered the "Incoming Connection" firewall prompt that
  blocked the UI from rendering. That polling loop has been removed — the
  responder now pushes received messages into the UI directly.

* `master.after(0, ...)` is used even for synchronous-looking UI updates so
  the call is always funneled through the Tk event loop.

* The window is explicitly sized and brought to the front at startup so it
  doesn't hide behind the Terminal on macOS.
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext


class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("CMP2204 P2P Chat")
        self.master.geometry("780x560")

        self.username = None
        self.peers = {}
        self._peers_lock = threading.Lock()

        bg_color = "#2b2b2b"
        fg_color = "#f0f0f0"
        entry_bg = "#3c3f41"
        button_bg = "#4b4f52"

        self.master.configure(bg=bg_color)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        # --- Username row -----------------------------------------------------
        username_frame = tk.Frame(self.master, bg=bg_color)
        username_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        tk.Label(username_frame, text="Username:", bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
        self.username_entry = tk.Entry(username_frame, bg=entry_bg, fg=fg_color, insertbackground=fg_color)
        self.username_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.username_entry.bind("<Return>", lambda _e: self.set_username())

        self.set_username_button = tk.Button(
            username_frame, text="Set Username",
            command=self.set_username,
            bg=button_bg, fg=fg_color,
            activebackground=button_bg, activeforeground=fg_color,
            highlightbackground=bg_color,
        )
        self.set_username_button.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Peer lists -------------------------------------------------------
        user_list_frame = tk.Frame(self.master, bg=bg_color)
        user_list_frame.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="ns")

        tk.Label(user_list_frame, text="Users Online", bg=bg_color, fg=fg_color).pack(anchor="w")
        self.user_list = tk.Listbox(
            user_list_frame, width=30, height=10,
            bg=entry_bg, fg=fg_color, selectbackground=button_bg, selectforeground=fg_color,
            exportselection=False,
        )
        self.user_list.pack(fill=tk.BOTH, expand=True)

        tk.Label(user_list_frame, text="Active Users", bg=bg_color, fg=fg_color).pack(anchor="w", pady=(8, 0))
        self.active_users_list = tk.Listbox(
            user_list_frame, width=30, height=10,
            bg=entry_bg, fg=fg_color, selectbackground=button_bg, selectforeground=fg_color,
            exportselection=False,
        )
        self.active_users_list.pack(fill=tk.BOTH, expand=True)

        # --- Chat display -----------------------------------------------------
        chat_frame = tk.Frame(self.master, bg=bg_color)
        chat_frame.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="nsew")

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, state="disabled",
            bg=entry_bg, fg=fg_color, insertbackground=fg_color,
            wrap="word",
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # --- Message input row ------------------------------------------------
        message_frame = tk.Frame(self.master, bg=bg_color)
        message_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.message_entry = tk.Entry(
            message_frame, bg=entry_bg, fg=fg_color, insertbackground=fg_color, state="disabled"
        )
        self.message_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", lambda _e: self.send_message())

        self.encrypt_var = tk.BooleanVar(value=True)
        self.encrypt_check = tk.Checkbutton(
            message_frame, text="Encrypt (DH)",
            variable=self.encrypt_var,
            bg=bg_color, fg=fg_color,
            activebackground=bg_color, activeforeground=fg_color,
            selectcolor=bg_color,  # macOS: matching bg avoids the white box glitch
            state="disabled",
        )
        self.encrypt_check.pack(side=tk.RIGHT)

        self.send_button = tk.Button(
            message_frame, text="Send",
            command=self.send_message,
            bg=button_bg, fg=fg_color,
            activebackground=button_bg, activeforeground=fg_color,
            highlightbackground=bg_color,
            state="disabled",
        )
        self.send_button.pack(side=tk.RIGHT, padx=10)

        self.load_chat_history()

        # Bring the window to front on macOS (often launches behind the Terminal).
        self.master.lift()
        self.master.attributes("-topmost", True)
        self.master.after(200, lambda: self.master.attributes("-topmost", False))
        self.username_entry.focus_set()

    # -------------------------------------------------------------------------
    # Username / UI state
    # -------------------------------------------------------------------------
    def set_username(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        self.username = username
        self.username_entry.config(state="disabled")
        self.set_username_button.config(state="disabled")
        self.message_entry.config(state="normal")
        self.send_button.config(state="normal")
        self.encrypt_check.config(state="normal")
        self.message_entry.focus_set()
        print(f"[ui] username set to: {self.username}")

    # -------------------------------------------------------------------------
    # Peer list — called from the discovery thread via master.after(...)
    # -------------------------------------------------------------------------
    def update_user_list(self, peers):
        with self._peers_lock:
            self.peers = dict(peers)
        self.user_list.delete(0, tk.END)
        self.active_users_list.delete(0, tk.END)
        for ip, (username, status) in self.peers.items():
            entry = f"{username} ({ip}) - {status}"
            self.user_list.insert(tk.END, entry)
            if status == "active":
                self.active_users_list.insert(tk.END, entry)

    # -------------------------------------------------------------------------
    # Sending
    # -------------------------------------------------------------------------
    def send_message(self):
        if not self.username:
            messagebox.showerror("Error", "You must set a username before sending messages.")
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        selected = self.user_list.curselection()
        if not selected:
            messagebox.showwarning("No peer", "Select a peer from the Users Online list first.")
            return

        selected_user = self.user_list.get(selected[0])
        try:
            peer_ip = selected_user.split("(", 1)[1].split(")", 1)[0]
        except IndexError:
            messagebox.showerror("Error", "Could not parse selected peer.")
            return

        secure = self.encrypt_var.get()

        # Do the network work off the UI thread.
        from eha_initiator import initiate_chat
        threading.Thread(
            target=initiate_chat,
            args=(self, self.username, peer_ip, message, 6001, secure),
            daemon=True,
        ).start()

        display_message = "<Encrypted>" if secure else message
        self.display_chat_message(self.username, display_message)
        self.store_message(self.username, display_message)
        self.message_entry.delete(0, tk.END)

    # -------------------------------------------------------------------------
    # Chat display + log persistence
    # -------------------------------------------------------------------------
    def display_chat_message(self, sender, message):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

    def store_message(self, sender, message):
        try:
            with open("chat.log", "a", encoding="utf-8") as log_file:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_file.write(f"{timestamp} - {sender}: {message}\n")
        except OSError as err:
            print(f"[ui] failed to write chat log: {err}")

    def load_chat_history(self):
        try:
            with open("chat.log", "r", encoding="utf-8") as log_file:
                for line in log_file:
                    try:
                        _, rest = line.rstrip("\n").split(" - ", 1)
                        sender, message = rest.split(": ", 1)
                        self.display_chat_message(sender, message)
                    except ValueError:
                        continue
        except FileNotFoundError:
            return
