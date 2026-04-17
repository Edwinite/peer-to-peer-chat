import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import socket
import json
from eha_announcer import service_announcer
from eha_discovery import peer_discovery
from eha_responder import chat_responder
from eha_initiator import initiate_chat
from encryption import decrypt_message

class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("P2P Chat")

        self.username = None  # Initially, there is no username
        self.peers = {}  # Store peers and their statuses

        # Define colors for dark mode compatibility
        bg_color = "#333333"
        fg_color = "#FFFFFF"
        entry_bg_color = "#555555"
        button_bg_color = "#444444"
        button_fg_color = "#FFFFFF"

        # Configure main window to expand correctly
        self.master.configure(bg=bg_color)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        # Create and pack the username frame
        self.username_frame = tk.Frame(self.master, bg=bg_color)
        self.username_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        print("Username frame created")

        # Create and pack the username label
        self.username_label = tk.Label(self.username_frame, text="Enter Username:", bg=bg_color, fg=fg_color)
        self.username_label.pack(side=tk.LEFT)
        print("Username label created")

        # Create and pack the username entry
        self.username_entry = tk.Entry(self.username_frame, bg=entry_bg_color, fg=fg_color)
        self.username_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
        print("Username entry created")

        # Create and pack the set username button
        self.set_username_button = tk.Button(self.username_frame, text="Set Username", command=self.set_username, bg=button_bg_color, fg=button_fg_color)
        self.set_username_button.pack(side=tk.RIGHT, padx=10, pady=10)
        print("Set Username button created")

        # Create and pack the user list frame
        self.user_list_frame = tk.Frame(self.master, bg=bg_color)
        self.user_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky='ns')
        print("User list frame created")

        # Create and pack the user list label
        self.user_list_label = tk.Label(self.user_list_frame, text="Users Online", bg=bg_color, fg=fg_color)
        self.user_list_label.pack()
        print("User list label created")

        # Create and pack the user list
        self.user_list = tk.Listbox(self.user_list_frame, width=30, height=10, bg=entry_bg_color, fg=fg_color)
        self.user_list.pack(fill=tk.BOTH, expand=True)
        print("User list created")

        # Create and pack the active users list label
        self.active_users_label = tk.Label(self.user_list_frame, text="Active Users", bg=bg_color, fg=fg_color)
        self.active_users_label.pack()
        print("Active users label created")

        # Create and pack the active users list
        self.active_users_list = tk.Listbox(self.user_list_frame, width=30, height=10, bg=entry_bg_color, fg=fg_color)
        self.active_users_list.pack(fill=tk.BOTH, expand=True)
        print("Active users list created")

        # Create and pack the chat frame
        self.chat_frame = tk.Frame(self.master, bg=bg_color)
        self.chat_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        print("Chat frame created")

        # Create and pack the chat display
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state='disabled', width=50, height=20, bg=entry_bg_color, fg=fg_color)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        print("Chat display created")

        # Create and pack the message entry frame
        self.message_frame = tk.Frame(self.master, bg=bg_color)
        self.message_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        print("Message frame created")

        # Create and pack the message entry
        self.message_entry = tk.Entry(self.message_frame, width=60, bg=entry_bg_color, fg=fg_color, state='disabled')  # Initially disabled
        self.message_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
        print("Message entry created")

        # Create and pack the send button
        self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message, bg=button_bg_color, fg=button_fg_color, state='disabled')  # Initially disabled
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)
        print("Send button created")

        # Create and pack the encrypt checkbox
        self.encrypt_var = tk.BooleanVar()
        self.encrypt_check = tk.Checkbutton(self.message_frame, text="Encrypt", variable=self.encrypt_var, bg=bg_color, fg=fg_color, selectcolor=entry_bg_color, state='disabled')  # Initially disabled
        self.encrypt_check.pack(side=tk.RIGHT, padx=10, pady=10)
        print("Encrypt checkbox created")

        self.load_chat_history()  # Load chat history

        # Start a thread to handle incoming messages
        threading.Thread(target=self.handle_incoming_messages, daemon=True).start()

    def set_username(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
        else:
            self.username = username
            self.username_entry.config(state='disabled')
            self.set_username_button.config(state='disabled')
            self.enable_chat()  # Enable chat components
            print(f"Username set to: {self.username}")

    def enable_chat(self):
        self.message_entry.config(state='normal')
        self.send_button.config(state='normal')
        self.encrypt_check.config(state='normal')

    def update_user_list(self, peers):
        self.peers = peers
        self.user_list.delete(0, tk.END)
        self.active_users_list.delete(0, tk.END)
        for ip, (username, status) in peers.items():
            user_entry = f"{username} ({ip}) - {status}"
            self.user_list.insert(tk.END, user_entry)
            if status == "active":
                self.active_users_list.insert(tk.END, user_entry)
        print("User list updated")

    def send_message(self):
        if not self.username:
            messagebox.showerror("Error", "You must set a username before sending messages.")
            return

        message = self.message_entry.get()
        selected_user = self.user_list.get(tk.ACTIVE)
        if selected_user:
            peer_ip = selected_user.split(' ')[1].strip('()')
            secure = self.encrypt_var.get()
            threading.Thread(target=initiate_chat, args=(self, self.username, peer_ip, message, 6001, secure), daemon=True).start()
            self.message_entry.delete(0, tk.END)
            # Only update the UI without logging
            display_message = "<Encrypted>" if secure else message
            self.display_chat_message(self.username, display_message)

    def display_chat_message(self, sender, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        print("Chat message displayed")

    def store_message(self, sender, message):
        with open('chat.log', 'a') as log_file:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            log_file.write(f"{timestamp} - {sender}: {message}\n")
        print(f"Message stored in log: {sender}: {message}")

    def load_chat_history(self):
        try:
            with open('chat.log', 'r') as log_file:
                for line in log_file:
                    try:
                        timestamp, message = line.strip().split(' - ', 1)
                        sender, message = message.split(': ', 1)
                        self.display_chat_message(sender, message)
                    except ValueError:
                        print(f"Skipping malformed log line: {line.strip()}")
        except FileNotFoundError:
            print("No chat history found.")

    def handle_incoming_messages(self):
        while True:
            # Check for new messages
            for peer_ip, (username, status) in self.peers.items():
                # Connect to each peer and check for new messages
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((peer_ip, 6001))
                        data = s.recv(1024)
                        if data:
                            message = json.loads(data.decode('utf-8'))
                            if 'unencrypted message' in message:
                                self.master.after(0, self.display_chat_message, username, message['unencrypted message'])
                                self.master.after(0, self.store_message, username, message['unencrypted message'])
                            elif 'encrypted message' in message:
                                decrypted_message = decrypt_message(message['encrypted message'])
                                self.master.after(0, self.display_chat_message, username, decrypted_message)
                                self.master.after(0, self.store_message, username, "<Encrypted>")
                except Exception as e:
                    print(f"Error connecting to peer {peer_ip}: {e}")
            time.sleep(1)

def main():
    root = tk.Tk()
    app = ChatApp(root)
    print("ChatApp initialized")

    def start_services():
        # Wait until the username is set
        while app.username is None:
            time.sleep(0.1)

        username = app.username

        # Start the necessary threads
        threading.Thread(target=service_announcer, args=(username,), daemon=True).start()
        threading.Thread(target=peer_discovery, args=(app,), daemon=True).start()
        threading.Thread(target=lambda: chat_responder(app), daemon=True).start()
        print("Threads started")

    threading.Thread(target=start_services, daemon=True).start()

    root.mainloop()

if __name__ == '__main__':
    main()
