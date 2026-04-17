import tkinter as tk
import threading
from eha_announcer import service_announcer
from eha_discovery import peer_discovery
from eha_responder import chat_responder
from eha_ui import ChatApp
import time

def main():
    global app
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
