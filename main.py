import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, Label, Frame
from tkinter.scrolledtext import ScrolledText
from normalise import normalize_log 
from collections import Counter
from tokenizer_pipeline import LogTokenizer
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from log_compare import setup_log_comparison_tab
import re

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

def open_file():
    # print("open_file() is running")

    file_path = filedialog.askopenfilename(
        filetypes=[("Log files", "*.log"), ("All files", "*.*")]
    )
    if not file_path:
        return
    
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        content = f.read()

    mod_ids = set()
    for line in content.splitlines():
        match = re.search(r"(?:/|\\)294100(?:/|\\)(\d{9,10})", line)
        if match:
            mod_ids.add(match.group(1))

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
    create_insights_tab(lines, filename, sub_notebook, raw_lines, mod_ids)

    # Tokenization debug paster
    # print(f"\n🔍 Tokenized Output for {filename}:")
    # for line_seq in sequences:
    #     print(line_seq)
    print("MOD IDS DETECTED:", mod_ids)

def create_insights_tab(normalized_lines, filename, sub_notebook, raw_lines, mod_ids):
    # print("create_insights_tab() is running")
    lines = normalized_lines
    is_rimworld_log = any(id_.isdigit() and len(id_) >= 9 for id_ in mod_ids)

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
    Label(scrollable_frame, text=f"Mods Detected: {len(mod_ids)}", font=("Arial", 10)).pack(anchor='w')

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

    Label(frame_mods, text="🧩 Workshop Mod IDs", font=("Arial", 12, 'bold')).pack(anchor='w')

    if mod_ids:
        for mod_id in sorted(mod_ids):
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

    # Bottom-right: Pie chart of placeholder counts
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
root = tk.Tk()
root.title("Multi-Log Viewer")
root.geometry("1000x700")
root.configure(bg='#A9B7C6')  # blue-grey

def on_closing():
    root.quit()    
    root.destroy() 

root.protocol("WM_DELETE_WINDOW", on_closing)

#top-level tab layout
main_tabs = ttk.Notebook(root)
main_tabs.pack(expand=1, fill="both")

# Tab 1: Single Log View
single_log_tab = ttk.Frame(main_tabs)
main_tabs.add(single_log_tab, text="Single Log View")

# Upload button inside Single Log View
upload_btn = tk.Button(single_log_tab, text="Upload Log File", command=open_file)
upload_btn.pack(pady=10)

# Sub-tabs for individual logs
tab_control = ttk.Notebook(single_log_tab)
tab_control.pack(expand=1, fill="both")

# Tab 2: Log Comparison (for the delta engine – empty for now)
compare_tab = ttk.Frame(main_tabs)
main_tabs.add(compare_tab, text="Log Comparison")

#Delta engine
setup_log_comparison_tab(compare_tab)

root.mainloop()