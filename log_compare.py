from tkinter import ttk, filedialog, Frame, Label, Button
import tkinter as tk
from mod_extractor import extract_mod_ids_from_log, extract_error_mods
import re

def setup_log_comparison_tab(parent_frame):
    frame = Frame(parent_frame)
    frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Container for buttons
    button_frame = Frame(frame)
    button_frame.pack(pady=10)

    # Upload buttons
    btn_a = Button(button_frame, text="Upload Log A", font=("Arial", 10), width=20, height=2, bg="#f0f0f0")
    btn_b = Button(button_frame, text="Upload Log B", font=("Arial", 10), width=20, height=2, bg="#f0f0f0")

    btn_a.grid(row=0, column=0, padx=30)
    btn_b.grid(row=0, column=1, padx=30)

    # Assign commands (pass the button reference too)
    btn_a.config(command=lambda: upload_log(frame, "A", btn_a))
    btn_b.config(command=lambda: upload_log(frame, "B", btn_b))

    # Output comparison panel
    output = Frame(frame)
    output.pack(fill='both', expand=True, pady=10)

    frame.output_area = output
    frame.logs = {}

def upload_log(parent_frame, label, button_ref):
    file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
    if not file_path:
        button_ref.configure(bg="#ffcccc") 
        return

    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            content = f.read()

        filename = file_path.split("/")[-1]  # or os.path.basename(file_path) if using os
        parent_frame.logs[label] = {
            "filename": filename,
            "content": content
        }
        button_ref.configure(bg="#ccffcc") 
    except Exception as e:
        print(f"Error loading {label}: {e}")
        button_ref.configure(bg="#ffcccc")
        return

    if "A" in parent_frame.logs and "B" in parent_frame.logs:
        compare_mod_mentions(parent_frame)

def compare_mod_mentions(frame):
    log_a = frame.logs["A"]
    log_b = frame.logs["B"]
    content_a = log_a["content"]
    content_b = log_b["content"]
    filename_a = log_a["filename"]
    filename_b = log_b["filename"]

    mod_ids_a = extract_mod_ids_from_log(content_a)
    mod_ids_b = extract_mod_ids_from_log(content_b)

    only_in_a = mod_ids_a - mod_ids_b
    only_in_b = mod_ids_b - mod_ids_a
    in_both = mod_ids_a & mod_ids_b
    for widget in frame.output_area.winfo_children():
        widget.destroy()

    # ───────────── Dual Pane View ─────────────
    dual_pane = Frame(frame.output_area)
    dual_pane.pack(fill='both', expand=True)

    # Create two side-by-side stat frames (Log A and B)
    log_a_frame = Frame(dual_pane, bd=2, relief='groove', padx=10, pady=10)
    log_b_frame = Frame(dual_pane, bd=2, relief='groove', padx=10, pady=10)
    log_a_frame.pack(side='left', expand=True, fill='both', padx=10)
    log_b_frame.pack(side='right', expand=True, fill='both', padx=10)

    # ───────────── LOG A ─────────────
    Label(log_a_frame, text=f"{filename_a}", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0, 10))
    Label(log_a_frame, text=f"Potential Culprit Mods: {len(mod_ids_a)}", font=("Arial", 10)).pack(anchor='w')
    if mod_ids_a:
        Label(log_a_frame, text="Mentioned Mods:", font=("Arial", 10, "underline")).pack(anchor='w', pady=(5, 0))
        for mod in sorted(mod_ids_a):
            Label(log_a_frame, text=f"• {mod}", font=("Arial", 9)).pack(anchor='w')

    # ───────────── LOG B ─────────────
    Label(log_b_frame, text=f"{filename_b}", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0, 10))
    Label(log_b_frame, text=f"Potential Culprit Mods: {len(mod_ids_b)}", font=("Arial", 10)).pack(anchor='w')
    if mod_ids_b:
        Label(log_b_frame, text="Mentioned Mods:", font=("Arial", 10, "underline")).pack(anchor='w', pady=(5, 0))
        for mod in sorted(mod_ids_b):
            Label(log_b_frame, text=f"• {mod}", font=("Arial", 9)).pack(anchor='w')

    # ───────────── Delta Section Below ─────────────
    Label(frame.output_area, text="Delta: Difference in Mod Mentions", font=("Arial", 12, "bold")).pack(anchor='w', pady=10)

    Label(frame.output_area, text=f"Only in Log A ({len(only_in_a)}):", font=("Arial", 10, "bold")).pack(anchor='w')
    for mod in sorted(only_in_a):
        Label(frame.output_area, text=f"• {mod}", font=("Arial", 9)).pack(anchor='w')

    Label(frame.output_area, text=f"Only in Log B ({len(only_in_b)}):", font=("Arial", 10, "bold")).pack(anchor='w', pady=(10, 0))
    for mod in sorted(only_in_b):
        Label(frame.output_area, text=f"• {mod}", font=("Arial", 9)).pack(anchor='w')

    if in_both:
        Label(frame.output_area, text=f"Shared Mod Mentions ({len(in_both)}):", font=("Arial", 10, "bold")).pack(anchor='w', pady=(10, 0))
        for mod in sorted(in_both):
            Label(frame.output_area, text=f"• {mod}", font=("Arial", 9)).pack(anchor='w')
