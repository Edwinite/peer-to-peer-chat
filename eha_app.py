import threading
import tkinter as tk

from eha_announcer import service_announcer
from eha_discovery import peer_discovery
from eha_responder import chat_responder
from eha_ui import ChatApp


def _start_services(app):
    # Wait until the user picks a username, then fire up the background services.
    while app.username is None:
        threading.Event().wait(0.1)

    username = app.username
    threading.Thread(target=service_announcer, args=(username,), daemon=True).start()
    threading.Thread(target=peer_discovery, args=(app,), daemon=True).start()
    threading.Thread(target=chat_responder, args=(app,), daemon=True).start()
    print(f"services started for user '{username}'")


def main():
    root = tk.Tk()
    app = ChatApp(root)
    threading.Thread(target=_start_services, args=(app,), daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()
