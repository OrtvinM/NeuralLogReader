from tkinterdnd2 import TkinterDnD
import tkinter as tk
import os
import json
from tkinter import filedialog, ttk, Toplevel, Label, Frame, Button
from tkinter.scrolledtext import ScrolledText
from normalise import normalize_log 
from collections import Counter
from tokenizer_pipeline import LogTokenizer
from smart_detector import load_model, load_tokenizer, predict_log
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from log_compare import setup_log_comparison_tab
from mod_extractor import extract_mod_ids_from_log, extract_error_mods
import re

mod_ids_loaded = set()
mod_names_loaded = set()
mod_names_in_errors = set()

def highlight_syntax(text_widget):
    # Define tag colors
    text_widget.tag_config("error", foreground="red")
    text_widget.tag_config("user", foreground="blue")
    text_widget.tag_config("ip", foreground="purple")
    text_widget.tag_config("timestamp", foreground="green")
    text_widget.tag_config("port", foreground="orange")
    text_widget.tag_config("path", foreground="darkgray")
    text_widget.tag_config("id", foreground="gray")
    text_widget.tag_config("engine_version", foreground="darkgreen")
    text_widget.tag_config("mod_patch", foreground="teal")
    text_widget.tag_config("duplicate_mod", foreground="orange")
    text_widget.tag_config("dll_fail", foreground="red")
    text_widget.tag_config("prepatcher_event", foreground="blue")

    content = text_widget.get("1.0", tk.END)

    # Clear old tags
    for tag in ["error", "user", "ip", "timestamp", "port", "path", "id"]:
        text_widget.tag_remove(tag, "1.0", tk.END)

    lines = content.split("\n")
    for i, line in enumerate(lines, start=1):
        for token, tag in [
            ("<engine_version>", "engine_version"),
            ("<mod_patch>", "mod_patch"),
            ("<duplicate_mod>", "duplicate_mod"),
            ("<dll_fail>", "dll_fail"),
            ("<prepatcher_event>", "prepatcher_event"),
            ("<error>", "error"),
            ("<user>", "user"),
            ("<ip>", "ip"),
            ("<timestamp>", "timestamp"),
            ("<port>", "port"),
            ("<path>", "path"),
            ("<id>", "id"),
        ]:
            if token in line:
                start_idx = f"{i}.0"
                while True:
                    pos = text_widget.search(token, start_idx, stopindex=f"{i}.end")
                    if not pos:
                        break
                    end_pos = f"{pos}+{len(token)}c"
                    text_widget.tag_add(tag, pos, end_pos)
                    start_idx = end_pos

def setup_smart_detector_tab(tab):
    # Split left and right frames
    frame_left = Frame(tab, bd=2, relief='groove')
    frame_left.pack(side='left', fill='both', expand=True, padx=10, pady=10)

    frame_right = Frame(tab, bd=2, relief='groove')
    frame_right.pack(side='right', fill='both', expand=True, padx=10, pady=10)

    # Left listbox
    Label(frame_left, text="Predictions", font=("Arial", 12, 'bold')).pack(anchor='w')
    tab.left_listbox = tk.Listbox(frame_left, font=("Arial", 11))
    tab.left_listbox.pack(expand=True, fill='both')

    # Upload button
    tab.detect_button = Button(frame_left, text="Detect Log", command=detect_log, font=("Arial", 11))
    tab.detect_button.pack(pady=10)

    # Right pie chart area
    Label(frame_right, text="Prediction Distribution", font=("Arial", 12, 'bold')).pack(anchor='w')
    tab.right_canvas_frame = Frame(frame_right)
    tab.right_canvas_frame.pack(expand=True, fill='both')

def draw_pie_chart(results):
    # Clear old chart
    for widget in smart_tab.right_canvas_frame.winfo_children():
        widget.destroy()

    # Create new pie chart
    labels = [tag for tag, prob in results if prob > 0.01]  # Only show >1% probs
    sizes = [prob for tag, prob in results if prob > 0.01]

    if not sizes:
        Label(smart_tab.right_canvas_frame, text="No significant predictions.").pack()
        return

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')

    pie_canvas = FigureCanvasTkAgg(fig, master=smart_tab.right_canvas_frame)
    pie_canvas.draw()
    pie_canvas.get_tk_widget().pack(fill='both', expand=True)

def detect_log():
    try:
        model = load_model()
        tokenizer = load_tokenizer()
    except Exception as e:
        tk.messagebox.showerror("Error", f"Failed to load model/tokenizer: {e}")
        return

    file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
    if not file_path:
        return

    with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
        raw_content = f.read()

    probs = predict_log(raw_content, model, tokenizer)
    if probs is None:
        tk.messagebox.showerror("Error", "Log file could not be processed.")
        return

    tag_options = [
        "Crash on Launch", "Crash Midgame", "Startup Errors",
        "Map Gen Error", "Minor Errors", "Graphical Bug", "Performance",
        "Mod Conflict", "Other", "Clean Log"
    ]

    results = list(zip(tag_options, probs))
    results.sort(key=lambda x: x[1], reverse=True)

    # Update listbox
    smart_tab.left_listbox.delete(0, tk.END)
    for tag, prob in results:
        smart_tab.left_listbox.insert(tk.END, f"{tag} ({prob:.2%})")
    draw_pie_chart(results)

def setup_ml_trainer_tab(trainer_tab):
    import tkinter as tk
    from tkinter import Label, Frame, Listbox, Button, filedialog
    from tkinterdnd2 import DND_FILES

    normalized_logs = {}
    uploaded_files = {} 

    files_frame = Frame(trainer_tab)
    files_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    tag_frame = Frame(trainer_tab)
    tag_frame.pack(side="right", fill="y", padx=10, pady=10)

    Label(files_frame, text="Uploaded Logs", font=("Arial", 12, "bold")).pack(anchor="nw")

    log_list = Listbox(files_frame, width=50, height=20, selectmode="extended")
    log_list.pack(fill="both", expand=True)

    selected_file_tags = {}
    current_selected = tk.StringVar(value="")

    tag_options = [
        "Crash on Launch", "Crash Midgame", "Startup Errors",
        "Map Gen Error", "Minor Errors", "Graphical Bug", "Performance",
        "Mod Conflict", "Other", "Clean Log"
    ]
    tag_checks = {}

    Label(tag_frame, text="Select Tags", font=("Arial", 12, "bold")).pack(anchor="nw")

    for tag in tag_options:
        var = tk.BooleanVar()
        cb = tk.Checkbutton(tag_frame, text=tag, variable=var)
        cb.pack(anchor="w")
        tag_checks[tag] = var

    def on_log_select(event):
        selection = log_list.curselection()
        if not selection:
            return
        filename = log_list.get(selection[0])
        current_selected.set(filename)

        # Load saved tags
        active_tags = selected_file_tags.get(filename, [])
        for tag, var in tag_checks.items():
            var.set(tag in active_tags)
        update_not_sure_bg()

    def upload_logs():
        try:
            file_paths = filedialog.askopenfilenames(
                filetypes=[("Log files", "*.log"), ("All files", "*.*")]
            )
            if not file_paths:
                return  # Cancel pressed, do nothing

            for path in file_paths:
                filename = os.path.basename(path)
                if filename not in log_list.get(0, tk.END):
                    log_list.insert("end", filename)
                    selected_file_tags[filename] = []
                    uploaded_files[filename] = path

        except Exception as e:
            print(f"Upload failed: {e}")

    def drop_handler(event):
        dropped_files = trainer_tab.tk.splitlist(event.data)
        for path in dropped_files:
            if path.lower().endswith(".log"):
                filename = path.split("/")[-1]
                if filename not in log_list.get(0, tk.END):
                    log_list.insert("end", filename)
                    selected_file_tags[filename] = []

    def confirm_tags():
        selections = log_list.curselection()
        if not selections:
            print("No log file selected.")
            return

        selected = [tag for tag, var in tag_checks.items() if var.get()]
        if "Not Sure" in selected:
            selected = [t for t in selected if t != "Not Sure"] + ["Not Sure"]

        for i in selections:
            filename = log_list.get(i)
            selected_file_tags[filename] = selected

            # Normalize content
            full_path = uploaded_files.get(filename)
            if full_path:
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        norm = normalize_log(content).splitlines()

                        tokenizer = LogTokenizer(max_length=20)
                        tokenizer.fit(norm)
                        sequences = tokenizer.transform(norm)
                        sequences = sequences.tolist() 

                        normalized_logs[filename] = {
                            "tags": selected,
                            "normalized": norm,
                            "tokenized": sequences
                        }
                        print(f"Log Assigned: {filename} → {selected}")

                except Exception as e:
                    print(f"Failed to read {filename}: {e}")

    log_list.bind('<<ListboxSelect>>', on_log_select)

    # Upload button
    Button(files_frame, text="Upload Log(s)", command=upload_logs, width=20).pack(pady=5)

    # Drag-and-drop label
    dnd_label = tk.Label(files_frame, text="Drop log files here", relief="ridge", borderwidth=2, width=40, height=3)
    dnd_label.pack(pady=10)

    def check_clipboard_drop():
        try:
            clipboard = trainer_tab.clipboard_get()
            if clipboard.endswith(".log") and clipboard not in log_list.get(0, tk.END):
                filename = clipboard.split("/")[-1] if "/" in clipboard else clipboard.split("\\")[-1]
                log_list.insert("end", filename)
                selected_file_tags[filename] = []
                print(f"🆕 Dropped: {filename}")
        except:
            pass
        trainer_tab.after(1000, check_clipboard_drop)
    Button(tag_frame, text="Confirm Tags", command=confirm_tags, width=20).pack(pady=(10, 5))

    # "Not Sure" 
    not_sure_var = tk.BooleanVar()

    not_sure_frame = Frame(tag_frame, bd=2, relief="groove")
    not_sure_frame.pack(fill="x", pady=(15, 5), padx=2)

    def update_not_sure_bg():
        if not_sure_var.get():
            not_sure_frame.configure(bg="#f5c6cb")
            not_sure_cb.configure(bg="#f5c6cb")
        else:
            not_sure_frame.configure(bg=tag_frame["bg"])
            not_sure_cb.configure(bg=tag_frame["bg"])

    not_sure_cb = tk.Checkbutton(
        not_sure_frame, text="Not Sure", variable=not_sure_var,
        command=update_not_sure_bg, anchor="w", relief="flat"
    )
    not_sure_cb.pack(fill="x", padx=5)

    tag_checks["Not Sure"] = not_sure_var

    def export_dataset():
        if not normalized_logs:
            print("No logs processed yet.")
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".jsonl",
            filetypes=[("JSON Lines", "*.jsonl")],
            title="Save Dataset As"
        )

        if not out_path:
            return

        try:
            output_dir = filedialog.askdirectory(title="Select Folder to Export JSON Files")
            if not output_dir:
                return

            try:
                for fname, data in normalized_logs.items():
                    safe_name = os.path.splitext(fname)[0].replace(" ", "_").replace(".", "_") + ".json"
                    output_path = os.path.join(output_dir, safe_name)

                    with open(output_path, 'w', encoding='utf-8') as f_out:
                        json.dump({
                            "filename": fname,
                            "tags": data["tags"],
                            "normalized": data["normalized"],
                            "tokenized": data["tokenized"]
                        }, f_out, indent=2)

                print(f"All logs exported individually to {output_dir}")
            except Exception as e:
                print(f"Failed to export: {e}")
            print(f"Dataset saved to {out_path}")
        except Exception as e:
            print(f"Failed to save dataset: {e}")
    Button(trainer_tab, text="Export Dataset", command=export_dataset, width=25).pack(pady=(10, 5))

def open_file():
    # print("open_file() is running")
    
    file_path = filedialog.askopenfilename(
        filetypes=[("Log files", "*.log"), ("All files", "*.*")]
    )
    if not file_path:
        return
    
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        content = f.read()

    mod_ids_loaded = extract_mod_ids_from_log(content)
    print("MOD IDS DETECTED:", mod_ids_loaded)

    raw_lines = content.splitlines()
    filename = file_path.split("/")[-1]

    # ───────────── Parent Tab for this log file ─────────────
    file_tab = ttk.Frame(tab_control)
    tab_control.add(file_tab, text=filename)

    # Sub-notebook for Raw / Clean / Graph
    sub_notebook = ttk.Notebook(file_tab)
    sub_notebook.pack(expand=1, fill='both')

    # ───────────── Raw Tab ─────────────
    raw_tab = ttk.Frame(sub_notebook)
    raw_text = ScrolledText(raw_tab, wrap='word', bg="#EAF0F6")
    raw_text.insert('1.0', content)
    raw_text.pack(expand=True, fill='both')
    sub_notebook.add(raw_tab, text="Raw")

    # ───────────── Clean Tab ─────────────
    normalized = normalize_log(content)
    clean_tab = ttk.Frame(sub_notebook)
    clean_text = ScrolledText(clean_tab, wrap='word', bg="#F0F0F0")
    clean_text.insert('1.0', normalized)
    clean_text.pack(expand=True, fill='both')
    sub_notebook.add(clean_tab, text="Clean")

    # Highlight normalized content
    highlight_syntax(clean_text)

    # Tokenize and print to terminal
    lines = normalized.split("\n")
    # print("Normalized preview:")
    # for l in lines[:10]:
    #     print(l)
    tokenizer = LogTokenizer(max_length=20)
    tokenizer.fit(lines)
    sequences = tokenizer.transform(lines)
    create_insights_tab(lines, filename, sub_notebook, raw_lines, mod_ids_loaded)

    # Tokenization debug paster
    # print(f"\n🔍 Tokenized Output for {filename}:")
    # for line_seq in sequences:
    #     print(line_seq)

def create_insights_tab(normalized_lines, filename, sub_notebook, raw_lines, mod_ids_loaded):
    # print("create_insights_tab() is running")
    lines = normalized_lines
    is_rimworld_log = any(id_.isdigit() and len(id_) >= 9 for id_ in mod_ids_loaded)

    # Create sub-notebook (nested tabs))
    sub_notebook.pack(expand=1, fill='both')

    # Graph tab inside sub-notebook
    graph_tab = ttk.Frame(sub_notebook)
    graph_tab.grid_rowconfigure((0, 1), weight=1)
    graph_tab.grid_columnconfigure((0, 1, 2), weight=1)
    sub_notebook.add(graph_tab, text="Graph")

    # Top-left: Log Summary (clean + scrollable)
    frame1 = Frame(graph_tab, bd=2, relief='groove')
    frame1.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

    canvas = tk.Canvas(frame1)
    scrollbar = tk.Scrollbar(frame1, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = Frame(canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    canvas.configure(yscrollcommand=scrollbar.set)

    # Summary labels
    Label(scrollable_frame, text="📄 Log Summary", font=("Arial", 12, 'bold')).pack(anchor='w')
    Label(scrollable_frame, text=f"Total Lines: {len(lines)}", font=("Arial", 10)).pack(anchor='w')
    Label(scrollable_frame, text=f"Unique Lines: {len(set(lines))}", font=("Arial", 10)).pack(anchor='w')
    Label(scrollable_frame, text=f"Mods Potentially Involved: {len(mod_ids_loaded)}", font=("Arial", 10)).pack(anchor='w')

    # Top-right: Token count
    frame2 = Frame(graph_tab, bd=2, relief='groove')
    frame2.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

    placeholder_tokens = [
        "<error>", "<notice>", "<timestamp>", "<ip>", "<port>", "<user>",
        "<duplicate_mod>", "<mod_missing_id>",
        "<mod_patch>", "<dll_fail>", "<prepatcher_event>", "<mod_config_warning>", "<mod_id>"
    ]
    placeholder_counts = Counter()

    for line in lines:
        for token in placeholder_tokens:
            if token in line:
                placeholder_counts[token] += 1

    Label(frame2, text="Placeholder Counts", font=("Arial", 12, 'bold')).pack(anchor='w')
    for token, count in placeholder_counts.items():
        Label(frame2, text=f"{token}: {count}").pack(anchor='w')

    # Middle-top: Workshop IDs
    frame_mods = Frame(graph_tab, bd=2, relief='groove')
    frame_mods.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)

    Label(frame_mods, text="Potential Culprit Mod IDs", font=("Arial", 12, 'bold')).pack(anchor='w')

    if mod_ids_loaded:
        for mod_id in sorted(mod_ids_loaded):
            Label(frame_mods, text=f"• {mod_id}").pack(anchor='w')
    else:
        Label(frame_mods, text="No mods detected.").pack(anchor='w')

    # Bottom-left: DLL Fail Heat map
    frame3 = Frame(graph_tab, bd=2, relief='groove')
    frame3.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

    if is_rimworld_log:
        print("RimWorld log detected — using DLL Fail Heatmap")
        Label(frame3, text="🧨 DLL Fail Heatmap", font=("Arial", 12, 'bold')).pack()

        dll_fail_bins = []
        for i, line in enumerate(raw_lines):
            if "fallback handler could not load library" in line.lower():
                dll_fail_bins.append(i // 20)

        bin_counts = Counter(dll_fail_bins)
        x_vals = sorted(bin_counts)
        y_vals = [bin_counts[x] for x in x_vals]

        if x_vals:
            fig3, ax3 = plt.subplots(figsize=(4, 2))
            ax3.plot(x_vals, y_vals)
            ax3.set_title("DLL Load Failures by Log Block")
            ax3.set_xlabel("Block (20 lines each)")
            ax3.set_ylabel("Failures")
            ax3.grid(True)

            canvas3 = FigureCanvasTkAgg(fig3, master=frame3)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill='both', expand=True)
        else:
            Label(frame3, text="No DLL failures detected.").pack()

    else:
        Label(frame3, text="Timestamp Frequency", font=("Arial", 12, 'bold')).pack()

        time_bins = []
        for i, line in enumerate(lines):
            if "<timestamp>" in line:
                time_bins.append(i // 20)

        bin_counts = Counter(time_bins)
        x_vals = sorted(bin_counts.keys())
        y_vals = [bin_counts[x] for x in x_vals]

        if x_vals:
            fig3, ax3 = plt.subplots(figsize=(4, 2))
            ax3.plot(x_vals, y_vals)
            ax3.set_ylim(bottom=0)
            ax3.grid(True)
            ax3.set_title("Timestamps by Log Block")
            ax3.set_xlabel("Block (20 lines each)")
            ax3.set_ylabel("Timestamp Occurrences")
            ax3.grid(True)

            canvas3 = FigureCanvasTkAgg(fig3, master=frame3)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill='both', expand=True)
        else:
            Label(frame3, text="No timestamps found in log.").pack()

    if not is_rimworld_log:
        timestamp_pattern = re.compile(
            r"\b(?:sun|mon|tue|wed|thu|fri|sat)? ?[a-z]{3} \d{1,2} \d{2}:\d{2}:\d{2}(?: \d{4})?\b",
            re.IGNORECASE
        )

        parsed_timestamps = []

        for line in raw_lines:
            match = timestamp_pattern.search(line)
            if match:
                ts = match.group()
                try:
                    dt = datetime.strptime(ts.strip(), "%a %b %d %H:%M:%S %Y")
                except ValueError:
                    try:
                        dt = datetime.strptime(ts.strip(), "%b %d %H:%M:%S")
                        dt = dt.replace(year=2000)
                    except ValueError:
                        continue
                parsed_timestamps.append(dt)

        if not parsed_timestamps:
            Label(frame3, text="No valid timestamps found in log.").pack()
        else:
            parsed_timestamps.sort()
            start_time = parsed_timestamps[0]
            end_time = parsed_timestamps[-1]
            total_range = end_time - start_time

            if total_range < timedelta(hours=1):
                bin_label = "Minute"
                round_to = lambda dt: dt.replace(second=0)
            elif total_range < timedelta(days=1):
                bin_label = "Hour"
                round_to = lambda dt: dt.replace(minute=0, second=0)
            else:
                bin_label = "Day"
                round_to = lambda dt: dt.replace(hour=0, minute=0, second=0)

            time_bins = [round_to(dt) for dt in parsed_timestamps]
            bin_counts = Counter(time_bins)
            x_vals = sorted(bin_counts.keys())
            y_vals = [bin_counts[x] for x in x_vals]

            fig2, ax2 = plt.subplots(figsize=(4.5, 2.5))
            ax2.plot(x_vals, y_vals)
            ax2.set_title(f"Log Entry Frequency by {bin_label}")
            ax2.set_xlabel(bin_label)
            ax2.set_ylabel("Entries")
            ax2.grid(True)
            fig2.autofmt_xdate()

            canvas2 = FigureCanvasTkAgg(fig2, master=frame3)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill='both', expand=True)

    # Bottom-right: Pie chart
    frame4 = Frame(graph_tab, bd=2, relief='groove')
    frame4.grid(row=1, column=2, sticky='nsew', padx=5, pady=5)
    Label(frame4, text="Placeholder Distribution", font=("Arial", 12, 'bold')).pack()

    labels = list(placeholder_counts.keys())
    sizes = list(placeholder_counts.values())

    if sizes:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')

        pie_canvas = FigureCanvasTkAgg(fig, master=frame4)
        pie_canvas.draw()
        pie_canvas.get_tk_widget().pack(fill='both', expand=True)
    else:
        Label(frame4, text="No placeholders found to graph.").pack()

# Create main window
root = TkinterDnD.Tk()
root.title("Multi-Log Viewer")
root.geometry("1000x700")
root.configure(bg='#A9B7C6')  # blue-grey

def on_closing():
    root.quit()    
    root.destroy() 

root.protocol("WM_DELETE_WINDOW", on_closing)

# Top-level tab layout
main_tabs = ttk.Notebook(root)
main_tabs.pack(expand=1, fill="both")

# Tab 1: Single Log View
single_log_tab = ttk.Frame(main_tabs)
main_tabs.add(single_log_tab, text="Single Log View")

upload_btn = tk.Button(single_log_tab, text="Upload Log File", command=open_file)
upload_btn.pack(pady=10)

tab_control = ttk.Notebook(single_log_tab)
tab_control.pack(expand=1, fill="both")

# Tab 2: Log Comparison
compare_tab = ttk.Frame(main_tabs)
main_tabs.add(compare_tab, text="Log Comparison")
setup_log_comparison_tab(compare_tab)

# Tab 3: Smart Detector
smart_tab = ttk.Frame(main_tabs)
main_tabs.add(smart_tab, text="Smart Detector")
setup_smart_detector_tab(smart_tab)

# Tab 4: ML Trainer
ml_trainer_tab = ttk.Frame(main_tabs)
main_tabs.add(ml_trainer_tab, text="ML Trainer")
setup_ml_trainer_tab(ml_trainer_tab)

# Start app loop
try:
    root.mainloop()
except tk.TclError:
    pass