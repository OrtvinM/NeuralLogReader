import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, Label, Frame
from tkinter.scrolledtext import ScrolledText
from normalise import normalize_log 
from collections import Counter
from tokenizer_pipeline import LogTokenizer
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def highlight_syntax(text_widget):
    # Define tag colors
    text_widget.tag_config("error", foreground="red")
    text_widget.tag_config("user", foreground="blue")
    text_widget.tag_config("ip", foreground="purple")
    text_widget.tag_config("timestamp", foreground="green")
    text_widget.tag_config("port", foreground="orange")
    text_widget.tag_config("path", foreground="darkgray")
    text_widget.tag_config("id", foreground="gray")

    content = text_widget.get("1.0", tk.END)

    # Clear old tags
    for tag in ["error", "user", "ip", "timestamp", "port", "path", "id"]:
        text_widget.tag_remove(tag, "1.0", tk.END)

    lines = content.split("\n")
    for i, line in enumerate(lines, start=1):
        for token, tag in [
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
    file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
    if not file_path:
        return

    with open(file_path, 'r') as f:
        content = f.read()

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
    tokenizer = LogTokenizer(max_length=20)
    tokenizer.fit(lines)
    sequences = tokenizer.transform(lines)

    # Tokenization debug paster
    # print(f"\n🔍 Tokenized Output for {filename}:")
    # for line_seq in sequences:
    #     print(line_seq)

    # ───────────── Graph Tab ─────────────
    graph_tab = ttk.Frame(sub_notebook)
    graph_tab.grid_rowconfigure((0, 1), weight=1)
    graph_tab.grid_columnconfigure((0, 1), weight=1)
    sub_notebook.add(graph_tab, text="Graph")

    # ───────────── Graph Subframes (2x2) ─────────────
    # Top-left: Summary
    frame1 = Frame(graph_tab, bd=2, relief='groove')
    frame1.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
    Label(frame1, text="📄 Log Summary", font=("Arial", 12, 'bold')).pack(anchor='w')
    Label(frame1, text=f"Total Lines: {len(lines)}").pack(anchor='w')
    Label(frame1, text=f"Unique Lines: {len(set(lines))}").pack(anchor='w')

    # Top-right: Placeholder token counts
    frame2 = Frame(graph_tab, bd=2, relief='groove')
    frame2.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
    Label(frame2, text="📌 Placeholder Counts", font=("Arial", 12, 'bold')).pack(anchor='w')

    placeholder_tokens = ["<error>", "<notice>", "<timestamp>", "<ip>", "<port>", "<id>", "<user>"]
    placeholder_counts = Counter()

    for line in lines:
        for token in placeholder_tokens:
            if token in line:
                placeholder_counts[token] += 1

    for token, count in placeholder_counts.items():
        Label(frame2, text=f"{token}: {count}").pack(anchor='w')

    # Bottom-left: Most common log lines
    frame3 = Frame(graph_tab, bd=2, relief='groove')
    frame3.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
    Label(frame3, text="📚 Most Common Lines", font=("Arial", 12, 'bold')).pack(anchor='w')

    line_freq = Counter(lines)
    for line, freq in line_freq.most_common(5):
        Label(frame3, text=f"[{freq}x] {line[:80]}").pack(anchor='w')

    # Bottom-right: Pie Chart
    frame4 = Frame(graph_tab, bd=2, relief='groove')
    frame4.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
    Label(frame4, text="📊 Placeholder Distribution", font=("Arial", 12, 'bold')).pack()

    labels = list(placeholder_counts.keys())
    sizes = list(placeholder_counts.values())

    if sizes:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        canvas = FigureCanvasTkAgg(fig, master=frame4)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    else:
        Label(frame4, text="No placeholder tokens found.").pack()

def create_insights_tab(normalized_lines, filename):
    lines = normalized_lines

    # Create a new file tab
    file_tab = ttk.Frame(tab_control)
    tab_control.add(file_tab, text=filename)

    # Create sub-notebook (nested tabs)
    sub_notebook = ttk.Notebook(file_tab)
    sub_notebook.pack(expand=1, fill='both')

    # Graph tab inside sub-notebook
    graph_tab = ttk.Frame(sub_notebook)
    graph_tab.grid_rowconfigure((0, 1), weight=1)
    graph_tab.grid_columnconfigure((0, 1), weight=1)
    sub_notebook.add(graph_tab, text="Graph")

    # Top-left: Log Summary + Most Common Lines
    frame1 = Frame(graph_tab, bd=2, relief='groove')
    frame1.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

    Label(frame1, text="📄 Log Summary", font=("Arial", 12, 'bold')).pack(anchor='w')
    Label(frame1, text=f"Total Lines: {len(lines)}").pack(anchor='w')
    Label(frame1, text=f"Unique Lines: {len(set(lines))}").pack(anchor='w')
    Label(frame1, text="Most Common Lines:", font=("Arial", 10, 'bold')).pack(anchor='w')
    line_freq = Counter(lines)
    for line, freq in line_freq.most_common(5):
        Label(frame1, text=f"[{freq}x] {line[:80]}").pack(anchor='w')

    # Top-right: Placeholder token counts
    frame2 = Frame(graph_tab, bd=2, relief='groove')
    frame2.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

    placeholder_tokens = ["<error>", "<notice>", "<timestamp>", "<ip>", "<port>", "<id>", "<user>"]
    placeholder_counts = Counter()

    for line in lines:
        for token in placeholder_tokens:
            if token in line:
                placeholder_counts[token] += 1

    Label(frame2, text="📌 Placeholder Counts", font=("Arial", 12, 'bold')).pack(anchor='w')
    for token, count in placeholder_counts.items():
        Label(frame2, text=f"{token}: {count}").pack(anchor='w')

    # Bottom-left: Timestamp timeline graph
    frame3 = Frame(graph_tab, bd=2, relief='groove')
    frame3.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
    Label(frame3, text="🕒 Timestamp Frequency", font=("Arial", 12, 'bold')).pack()

    time_bins = []
    for i, line in enumerate(lines):
        if "<timestamp>" in line:
            time_bins.append(i // 20)

    bin_counts = Counter(time_bins)
    x_vals = sorted(bin_counts.keys())
    y_vals = [bin_counts[x] for x in x_vals]

    if x_vals:
        fig2, ax2 = plt.subplots(figsize=(4, 2))
        ax2.plot(x_vals, y_vals, marker='o')
        ax2.set_title("Timestamps by Log Block")
        ax2.set_xlabel("Block (20 lines each)")
        ax2.set_ylabel("Timestamp Occurrences")
        ax2.grid(True)

        canvas2 = FigureCanvasTkAgg(fig2, master=frame3)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill='both', expand=True)
    else:
        Label(frame3, text="No timestamps found in log.").pack()

    # Bottom-right: Pie chart of placeholder counts
    frame4 = Frame(graph_tab, bd=2, relief='groove')
    frame4.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
    Label(frame4, text="📊 Placeholder Distribution", font=("Arial", 12, 'bold')).pack()

    labels = list(placeholder_counts.keys())
    sizes = list(placeholder_counts.values())

    if sizes:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')

        canvas = FigureCanvasTkAgg(fig, master=frame4)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
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

# Upload Button
upload_btn = tk.Button(root, text="Upload Log File", command=open_file)
upload_btn.pack(pady=10)

# Tabbed notebook for multi-file viewing
tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both")

root.mainloop()
