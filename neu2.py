import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import re
import os
import webbrowser
from pyvis.network import Network

# Set UI Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class HighPerformanceAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ultra-Fast Multi-Log Analyzer & Link Intel")
        self.geometry("1400x900")
        self.minsize(1200, 700)

        self.parsed_data = []
        self.filtered_data = []
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="LogMaster Pro", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))

        # Core Actions
        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="1. Load Multiple Logs", command=self.load_files, height=40)
        self.load_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.network_btn = ctk.CTkButton(self.sidebar_frame, text="2. Advanced Link Analysis", command=self.generate_network_graph, height=40, fg_color="#D35400", hover_color="#A04000")
        self.network_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Exports
        self.export_txt_btn = ctk.CTkButton(self.sidebar_frame, text="Export as TXT", command=self.export_txt, fg_color="#8E44AD", hover_color="#732D91")
        self.export_txt_btn.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Dashboard Stats
        self.stats_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.stats_frame.grid(row=4, column=0, padx=20, pady=20, sticky="w")
        
        self.lbl_total = ctk.CTkLabel(self.stats_frame, text="Total Loaded: 0", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_total.pack(anchor="w", pady=2)
        
        self.lbl_success = ctk.CTkLabel(self.stats_frame, text="Success/Sent: 0", text_color="#4CAF50", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_success.pack(anchor="w", pady=2)

        self.lbl_error = ctk.CTkLabel(self.stats_frame, text="Errors/Rejected: 0", text_color="#F44336", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_error.pack(anchor="w", pady=2)

        # --- Main Content ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Advanced Filters Bar
        self.filter_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.apply_filters) # Real-time filtering
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Search globally (Details, IP, Sender)...", textvariable=self.search_var, width=350)
        self.search_entry.pack(side="left", padx=15, pady=15)

        self.status_var = ctk.StringVar(value="All Status")
        self.status_menu = ctk.CTkOptionMenu(self.filter_frame, variable=self.status_var, values=["All Status", "Success", "Error", "Info"], command=self.apply_filters)
        self.status_menu.pack(side="left", padx=15, pady=15)

        # Table (Treeview)
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("Timestamp", "Status", "Source (From)", "Destination (To)", "Full Details")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="extended")

        # Treeview Styling & Colors
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="#e0e0e0", rowheight=30, fieldbackground="#2b2b2b")
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

        # Configure Tags for Row Colors
        self.tree.tag_configure('Success', foreground='#4CAF50') # Green
        self.tree.tag_configure('Error', foreground='#F44336')   # Red
        self.tree.tag_configure('Info', foreground='#9E9E9E')    # Gray

        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.column("Timestamp", width=150, stretch=False)
        self.tree.column("Status", width=100, anchor="center", stretch=False)
        self.tree.column("Source (From)", width=220, stretch=False)
        self.tree.column("Destination (To)", width=220, stretch=False)
        self.tree.column("Full Details", width=500, stretch=True) # Takes remaining space

        self.tree.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")

        x_scroll = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=x_scroll.set)
        x_scroll.grid(row=2, column=0, sticky="ew")

    def load_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Log Files", filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepaths:
            self.parse_logs(filepaths)

    def parse_logs(self, filepaths):
        self.parsed_data = []
        
        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                    for line in file:
                        line = line.strip()
                        if not line: continue

                        timestamp, status_cat, source, dest, details = "N/A", "Info", "N/A", "N/A", line
                        
                        # --- Pattern 1: New HAProxy / SCCM XML-like Format ---
                        if "<![LOG[" in line:
                            # Extract Message
                            msg_match = re.search(r'<!\[LOG\[(.*?)\] LOG\]!', line)
                            msg = msg_match.group(1).strip() if msg_match else ""
                            
                            # Extract Date and Time (handling weird quotes like „ “ or standard " ')
                            date_match = re.search(r'date=["\'„“]([^"\'„“]+)["\'„“]', line)
                            time_match = re.search(r'time=["\'„“]([^"\'„“\-]+)', line) # Ignore timezone offset for cleaner view
                            
                            d_str = date_match.group(1) if date_match else ""
                            t_str = time_match.group(1) if time_match else ""
                            timestamp = f"{d_str} {t_str}".strip() if d_str or t_str else "Unknown"

                            details = msg
                            
                            # Extract IPs from Connect strings (Supports IPv4 and IPv6)
                            conn_match = re.search(r'Connect from ([\w:]+) to ([\w:]+)', msg, re.IGNORECASE)
                            if conn_match:
                                source = conn_match.group(1)
                                dest = conn_match.group(2)
                                status_cat = "Success" # A connection attempt is generally a success in this context
                            
                            # Check for errors in msg
                            if any(err in msg.lower() for err in ["error", "reject", "fail", "timeout", "drop"]):
                                status_cat = "Error"

                        # --- Pattern 2: Standard Postfix Format ---
                        elif "postfix" in line.lower() or "smtpd" in line.lower():
                            time_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                            timestamp = time_match.group(1) if time_match else "Unknown"

                            sender_match = re.search(r'from=<([^>]+)>', line)
                            source = sender_match.group(1) if sender_match else "N/A"

                            recipient_match = re.search(r'to\s*=?\s*<([^>]+)>', line)
                            dest = recipient_match.group(1) if recipient_match else "N/A"

                            ip_match = re.search(r'\[([0-9a-fA-F\.\:]+)\]', line) # IPv4 & IPv6
                            if ip_match and source == "N/A": 
                                source = ip_match.group(1) # Fallback source to IP if no email

                            if "reject:" in line.lower() or "bounced" in line.lower() or "failed" in line.lower():
                                status_cat = "Error"
                            elif "status=sent" in line.lower() or "delivered" in line.lower():
                                status_cat = "Success"
                            
                            details = line

                        # Only add if it has meaningful data
                        if status_cat != "Info" or source != "N/A" or dest != "N/A":
                            self.parsed_data.append((timestamp, status_cat, source, dest, details))

            except Exception as e:
                print(f"Error parsing file {filepath}: {e}")

        self.apply_filters()
        messagebox.showinfo("Success", f"Successfully loaded and parsed {len(self.parsed_data)} records from {len(filepaths)} file(s).")

    def apply_filters(self, *args):
        query = self.search_var.get().lower()
        status_filter = self.status_var.get()

        self.filtered_data = []
        for row in self.parsed_data:
            # Row mapping: 0:Time, 1:Status, 2:Source, 3:Dest, 4:Details
            
            # Status Filter
            if status_filter != "All Status" and row[1] != status_filter:
                continue
            
            # Global Search Filter (Search inside Details, Source, or Dest)
            if query and not (query in row[4].lower() or query in row[2].lower() or query in row[3].lower()):
                continue
            
            self.filtered_data.append(row)

        self.populate_table(self.filtered_data)
        self.update_stats(self.filtered_data)

    def populate_table(self, data):
        self.tree.delete(*self.tree.get_children())
        for row in data:
            status_tag = row[1] # "Success", "Error", or "Info"
            self.tree.insert("", "end", values=row, tags=(status_tag,))

    def update_stats(self, data):
        total = len(data)
        success = sum(1 for row in data if row[1] == "Success")
        error = sum(1 for row in data if row[1] == "Error")

        self.lbl_total.configure(text=f"Total Displayed: {total}")
        self.lbl_success.configure(text=f"Success/Sent: {success}")
        self.lbl_error.configure(text=f"Errors/Rejected: {error}")

    # --- Enhanced Link Analysis ---
    def generate_network_graph(self):
        if not self.filtered_data:
            messagebox.showwarning("Warning", "No data to analyze.")
            return

        try:
            net = Network(height='100vh', width='100%', bgcolor='#121212', font_color='white', directed=True)
            net.force_atlas_2based()

            nodes_added = set()

            for row in self.filtered_data:
                status, source, dest, details = row[1], row[2], row[3], row[4]

                if source == "N/A" or dest == "N/A": continue

                edge_color = '#4CAF50' if status == "Success" else '#F44336'

                # Clean up nodes
                if source not in nodes_added:
                    shape = "hexagon" if ":" in source or "." in source else "dot" # IP vs Email
                    net.add_node(source, label=source, title="Source Entity", color='#3498DB', size=25, shape=shape)
                    nodes_added.add(source)

                if dest not in nodes_added:
                    shape = "hexagon" if ":" in dest or "." in dest else "dot"
                    net.add_node(dest, label=dest, title="Destination Entity", color='#9B59B6', size=25, shape=shape)
                    nodes_added.add(dest)

                # Link them with details on hover
                net.add_edge(source, dest, color=edge_color, title=f"[{status}]\n{details[:100]}...")

            graph_path = os.path.abspath("advanced_network.html")
            net.write_html(graph_path)
            webbrowser.open(f"file://{graph_path}")
            
        except Exception as e:
            messagebox.showerror("Graph Error", f"Could not generate network graph:\n{e}")

    # --- Export to TXT ---
    def export_txt(self):
        if not self.filtered_data: return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")], title="Export as TXT")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("="*100 + "\n")
                    f.write(f"{'TIMESTAMP':<25} | {'STATUS':<10} | {'SOURCE':<35} | {'DESTINATION':<35}\n")
                    f.write("="*100 + "\n")
                    
                    for row in self.filtered_data:
                        f.write(f"{row[0]:<25} | {row[1]:<10} | {row[2]:<35} | {row[3]:<35}\n")
                        f.write(f"DETAILS: {row[4]}\n")
                        f.write("-" * 100 + "\n")
                        
                messagebox.showinfo("Success", "Data successfully exported to TXT format!")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to write text file:\n{e}")

if __name__ == "__main__":
    app = HighPerformanceAnalyzer()
    app.mainloop()
