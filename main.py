import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from normalise import normalize_log 

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

        # Original log tab (no highlighting)
        original_tab = ttk.Frame(tab_control)
        original_text = ScrolledText(original_tab, wrap=tk.WORD, bg="#EAF0F6")
        original_text.insert(tk.END, content)
        original_text.pack(expand=True, fill='both')
        tab_control.add(original_tab, text=filename)

        # Normalized log tab (with highlighting!)
        normalized_tab = ttk.Frame(tab_control)
        normalized_text = ScrolledText(normalized_tab, wrap=tk.WORD, bg="#F0F0F0")
        normalized = normalize_log(content)
        normalized_text.insert(tk.END, normalized)
        normalized_text.pack(expand=True, fill='both')
        tab_control.add(normalized_tab, text=f"{filename} (clean)")

        highlight_syntax(normalized_text)  # <-- Apply highlighting only to normalized

# Create main window
root = tk.Tk()
root.title("Multi-Log Viewer")
root.geometry("1000x700")
root.configure(bg='#A9B7C6')  # bluish-grey

# Upload Button
upload_btn = tk.Button(root, text="Upload Log File", command=open_file)
upload_btn.pack(pady=10)

# Tabbed notebook for multi-file viewing
tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both")

root.mainloop()
