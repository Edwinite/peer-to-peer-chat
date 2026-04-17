"""
Entry point for the CMP2204 P2P chat.

Layout:

  main()              -- creates the Tk root and UI, then waits for the user
                         to set a username. Once set, it starts three daemon
                         threads: announcer, discovery, and responder.

  Tk mainloop runs on the MAIN thread (required on macOS). Everything else
  runs on daemon threads so the app exits cleanly when the window closes.
"""

import threading
import tkinter as tk

from eha_announcer import service_announcer
from eha_discovery import peer_discovery
from eha_responder import chat_responder
from eha_ui import ChatApp


def _wait_for_username_then_start_services(app):
    # Busy-wait with short sleeps is fine here: this is a daemon thread and
    # runs at most until the user types their username.
    app.master.wait_variable = getattr(app.master, "wait_variable", None)
    while app.username is None:
        threading.Event().wait(0.1)

    username = app.username
    threading.Thread(target=service_announcer, args=(username,), daemon=True).start()
    threading.Thread(target=peer_discovery, args=(app,), daemon=True).start()
    threading.Thread(target=chat_responder, args=(app,), daemon=True).start()
    print(f"[app] services started for user '{username}'")


def main():
    root = tk.Tk()
    app = ChatApp(root)
    threading.Thread(
        target=_wait_for_username_then_start_services,
        args=(app,),
        daemon=True,
    ).start()
    root.mainloop()


if __name__ == "__main__":
    main()
