# Quick Tk check - prints versions and opens a tiny test window.

import sys
import tkinter as tk
from tkinter import ttk


def main():
    root = tk.Tk()
    root.title("Tk diagnostic")
    root.geometry("420x280")

    tk_version = root.tk.call("info", "patchlevel")
    print(f"Python : {sys.version.split()[0]}")
    print(f"Tcl/Tk : {tk_version}")
    print(f"Themes : {list(ttk.Style().theme_names())}")
    print(f"Theme  : {ttk.Style().theme_use()}")

    tk.Label(root, text=f"Tk {tk_version} - if you can read this, labels work").pack(pady=10)

    entry = tk.Entry(root)
    entry.insert(0, "type here")
    entry.pack(fill="x", padx=20, pady=5)

    status = tk.Label(root, text="Status", relief="groove", anchor="w")

    def on_click():
        status.config(text=f"Button works. Entry: {entry.get()!r}")

    tk.Button(root, text="Click me", command=on_click).pack(pady=10)
    status.pack(fill="x", padx=20, pady=10)

    root.lift()
    root.attributes("-topmost", True)
    root.after(300, lambda: root.attributes("-topmost", False))
    root.mainloop()


if __name__ == "__main__":
    main()
