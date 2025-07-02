import tkinter as tk

def run_rules_window():
    rules = [
        "1 finger up (hold 3s): Fold",
        "2 fingers up (hold 3s): Call/Check",
        "3 fingers up (hold 3s): Raise",
        "4 fingers up (hold 3s): All-in",
        "5 fingers up (hold 3s): Show cards"
    ]
    root = tk.Tk()
    root.title("Poker Gesture Rules")
    for rule in rules:
        tk.Label(root, text=rule, font=("Arial", 14)).pack(anchor="w")
    root.geometry("320x180+850+100")
    root.mainloop()