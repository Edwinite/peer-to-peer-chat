import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext


class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("CMP2204 P2P Chat")
        self.master.geometry("820x580")
        self.master.minsize(700, 440)

        self.username = None
        self.peers = {}
        self._peers_lock = threading.Lock()

        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, minsize=230)
        self.master.grid_columnconfigure(1, weight=1)

        # Username row
        username_frame = tk.Frame(self.master)
        username_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 6))
        username_frame.grid_columnconfigure(1, weight=1)

        tk.Label(username_frame, text="Username:").grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.username_entry = tk.Entry(username_frame)
        self.username_entry.grid(row=0, column=1, sticky="ew")
        self.username_entry.bind("<Return>", lambda _e: self.set_username())

        self.set_username_button = tk.Button(
            username_frame, text="Set Username", command=self.set_username,
        )
        self.set_username_button.grid(row=0, column=2, padx=(8, 0))

        # Peer list column
        peers_frame = tk.Frame(self.master)
        peers_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=6)
        peers_frame.grid_rowconfigure(1, weight=1)
        peers_frame.grid_rowconfigure(3, weight=1)
        peers_frame.grid_columnconfigure(0, weight=1)

        tk.Label(peers_frame, text="Users Online").grid(row=0, column=0, sticky="w")
        self.user_list = tk.Listbox(
            peers_frame, height=8, exportselection=False, activestyle="dotbox",
        )
        self.user_list.grid(row=1, column=0, sticky="nsew", pady=(2, 8))

        tk.Label(peers_frame, text="Active Users").grid(row=2, column=0, sticky="w")
        self.active_users_list = tk.Listbox(
            peers_frame, height=8, exportselection=False, activestyle="dotbox",
        )
        self.active_users_list.grid(row=3, column=0, sticky="nsew", pady=(2, 0))

        # Chat display column
        chat_frame = tk.Frame(self.master)
        chat_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=6)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, state="disabled", wrap="word", height=18,
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        # Message row
        message_frame = tk.Frame(self.master)
        message_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(6, 10))
        message_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = tk.Entry(message_frame)
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.message_entry.bind("<Return>", lambda _e: self.send_message())
        self.message_entry.config(state="disabled")

        self.encrypt_var = tk.BooleanVar(value=True)
        self.encrypt_check = tk.Checkbutton(
            message_frame, text="Encrypt (DH)", variable=self.encrypt_var, state="disabled",
        )
        self.encrypt_check.grid(row=0, column=1, padx=(0, 8))

        self.send_button = tk.Button(
            message_frame, text="Send", command=self.send_message, state="disabled",
        )
        self.send_button.grid(row=0, column=2)

        self.load_chat_history()

        # Pull the window to the foreground (on macOS it often opens behind Terminal).
        self.master.update_idletasks()
        self.master.lift()
        self.master.attributes("-topmost", True)
        self.master.after(250, lambda: self.master.attributes("-topmost", False))
        self.username_entry.focus_set()

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
        print(f"username set to: {self.username}")

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
            print(f"failed to write chat log: {err}")

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
