import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, Label, Frame
from tkinter.scrolledtext import ScrolledText
from normalise import normalize_log 
from collections import Counter
from tokenizer_pipeline import LogTokenizer

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
    if file_path:
        with open(file_path, 'r') as f:
            content = f.read()

        filename = file_path.split("/")[-1]

        #Original tab
        original_tab = ttk.Frame(tab_control)
        original_text = ScrolledText(original_tab, wrap=tk.WORD, bg="#EAF0F6")
        original_text.insert(tk.END, content)
        original_text.pack(expand=True, fill='both')
        tab_control.add(original_tab, text=filename)

        # Normalized tab
        normalized_tab = ttk.Frame(tab_control)
        normalized_text = ScrolledText(normalized_tab, wrap=tk.WORD, bg="#F0F0F0")
        normalized = normalize_log(content)
        create_insights_tab(normalized.split("\n"), filename)
        normalized_text.insert(tk.END, normalized)
        normalized_text.pack(expand=True, fill='both')
        tab_control.add(normalized_tab, text=f"{filename} (clean)")
        highlight_syntax(normalized_text)

        #Tokenize and print to terminal
        lines = normalized.split("\n")
        tokenizer = LogTokenizer(max_length=20)
        tokenizer.fit(lines)  
        sequences = tokenizer.transform(lines)

        print("\n🔍 Tokenized Output:")
        for line_seq in sequences:
            print(line_seq)

def create_insights_tab(normalized_lines, filename):
    insights_tab = ttk.Frame(tab_control)
    tab_control.add(insights_tab, text=f"{filename} (graph)")

    insights_tab.grid_rowconfigure((0, 1), weight=1)
    insights_tab.grid_columnconfigure((0, 1), weight=1)

    # Top-left: Log summary
    frame1 = Frame(insights_tab, bd=2, relief='groove')
    frame1.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

    total_lines = len(normalized_lines)
    unique_lines = len(set(normalized_lines))

    Label(frame1, text="📄 Log Summary", font=("Arial", 12, 'bold')).pack(anchor='w')
    Label(frame1, text=f"Total Lines: {total_lines}").pack(anchor='w')
    Label(frame1, text=f"Unique Lines: {unique_lines}").pack(anchor='w')

    # Top-right: Placeholder token counts
    frame2 = Frame(insights_tab, bd=2, relief='groove')
    frame2.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

    placeholder_tokens = ["<error>", "<notice>", "<timestamp>", "<ip>", "<port>", "<id>", "<user>"]
    placeholder_counts = Counter()

    for line in normalized_lines:
        for token in placeholder_tokens:
            if token in line:
                placeholder_counts[token] += 1

    Label(frame2, text="📌 Placeholder Counts", font=("Arial", 12, 'bold')).pack(anchor='w')
    for token, count in placeholder_counts.items():
        Label(frame2, text=f"{token}: {count}").pack(anchor='w')

    # Bottom-left: Most common lines
    frame3 = Frame(insights_tab, bd=2, relief='groove')
    frame3.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

    line_freq = Counter(normalized_lines)
    Label(frame3, text="📚 Most Common Lines", font=("Arial", 12, 'bold')).pack(anchor='w')

    for line, freq in line_freq.most_common(5):
        Label(frame3, text=f"[{freq}x] {line[:80]}").pack(anchor='w')

    # Bottom-right: Placeholder for the future graph
    frame4 = Frame(insights_tab, bd=2, relief='groove')
    frame4.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

    Label(frame4, text="📊 Graphs coming soon", font=("Arial", 12, 'italic')).pack(anchor='center')

# Create main window
root = tk.Tk()
root.title("Multi-Log Viewer")
root.geometry("1000x700")
root.configure(bg='#A9B7C6')  # blue-grey

# Upload Button
upload_btn = tk.Button(root, text="Upload Log File", command=open_file)
upload_btn.pack(pady=10)

# Tabbed notebook for multi-file viewing
tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both")

root.mainloop()
