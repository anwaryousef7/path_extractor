import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import re
import socket
import requests
import threading
import tkintermapview

# Set UI Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UltimateLogAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LogMaster Pro - Ultimate Filter & Geo Analyzer")
        self.geometry("1450x950")
        self.minsize(1200, 800)

        self.parsed_data = []
        self.filtered_data = []
        self.row_details_map = {}
        
        # Regex patterns for Highlighting & Extraction
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[A-Fa-f0-9]{1,4}:){1,7}[A-Fa-f0-9]{1,4}\b'
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="LogMaster Pro", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=30, padx=20)
        
        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="1. Load Log Files", command=self.load_files, height=45)
        self.load_btn.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        
        self.export_btn = ctk.CTkButton(self.sidebar_frame, text="2. Export to TXT", command=self.export_txt, height=45, fg_color="#8E44AD", hover_color="#732D91")
        self.export_btn.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

        # Dashboard Stats
        self.stats_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, padx=20, pady=30, sticky="w")
        
        self.lbl_total = ctk.CTkLabel(self.stats_frame, text="Total Records: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_total.pack(anchor="w", pady=5)
        
        self.lbl_success = ctk.CTkLabel(self.stats_frame, text="Success/Sent: 0", text_color="#4CAF50", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_success.pack(anchor="w", pady=5)
        
        self.lbl_error = ctk.CTkLabel(self.stats_frame, text="Errors/Rejected: 0", text_color="#F44336", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_error.pack(anchor="w", pady=5)

        self.lbl_info = ctk.CTkLabel(self.stats_frame, text="Information: 0", text_color="#9E9E9E", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_info.pack(anchor="w", pady=5)

        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_frame.grid_rowconfigure(1, weight=1) 
        self.main_frame.grid_rowconfigure(2, weight=1) 
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 1. Advanced Top Filter Bar
        self.filter_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.apply_filters)
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Live Search: IP, Email, or Error details...", textvariable=self.search_var, width=400, height=35)
        self.search_entry.pack(side="left", padx=15, pady=15)

        self.status_var = ctk.StringVar(value="All Status")
        self.status_menu = ctk.CTkOptionMenu(self.filter_frame, variable=self.status_var, values=["All Status", "Success", "Error", "Info"], command=self.apply_filters, width=150, height=35)
        self.status_menu.pack(side="left", padx=15, pady=15)

        # 2. Treeview (Table)
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        columns = ("Timestamp", "Status", "Source (From)", "Destination (To)")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="#e0e0e0", rowheight=32, fieldbackground="#2b2b2b", font=('Segoe UI', 10))
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

        self.tree.tag_configure('Success', foreground='#4CAF50')
        self.tree.tag_configure('Error', foreground='#F44336')
        self.tree.tag_configure('Info', foreground='#9E9E9E')

        for col in columns: self.tree.heading(col, text=col)
        self.tree.column("Timestamp", width=180, anchor="w")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.column("Source (From)", width=300, anchor="w")
        self.tree.column("Destination (To)", width=300, anchor="w")
        
        self.tree.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # 3. Bottom Area: Inspector + Map
        self.bottom_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_panel.grid(row=2, column=0, sticky="nsew")
        self.bottom_panel.grid_columnconfigure(0, weight=3) # Details gets more space
        self.bottom_panel.grid_columnconfigure(1, weight=2) # Map gets less space

        # Left: Full Details Textbox
        self.details_frame = ctk.CTkFrame(self.bottom_panel)
        self.details_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(self.details_frame, text="Contextual Log Details (IP & Email Highlighted)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.details_box = ctk.CTkTextbox(self.details_frame, font=("Consolas", 14), wrap="word", spacing1=2, spacing3=2)
        self.details_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.details_box.tag_config("ip_highlight", foreground="#F39C12", font=("Consolas", 14, "bold")) # Orange
        self.details_box.tag_config("email_highlight", foreground="#3498DB", font=("Consolas", 14, "bold")) # Blue

        # Right: Map View
        self.geo_frame = ctk.CTkFrame(self.bottom_panel)
        self.geo_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.geo_label = ctk.CTkLabel(self.geo_frame, text="Geolocation Tracker (IP or Domain)", font=ctk.CTkFont(weight="bold"))
        self.geo_label.pack(pady=5)
        
        self.map_widget = tkintermapview.TkinterMapView(self.geo_frame, corner_radius=10)
        self.map_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(1)

    def load_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Multiple Log Files")
        if filepaths: self.parse_logs(filepaths)

    def parse_logs(self, filepaths):
        self.parsed_data = []
        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                    for line in file:
                        line = line.strip()
                        if not line: continue

                        timestamp, status, source, dest, details = "N/A", "Info", "N/A", "N/A", line
                        
                        # Format 1: HAProxy / SCCM
                        if "<![LOG[" in line:
                            msg_match = re.search(r'<!\[LOG\[(.*?)\] LOG\]!', line)
                            msg = msg_match.group(1).strip() if msg_match else ""
                            date_match = re.search(r'date=["\'„“]([^"\'„“]+)["\'„“]', line)
                            time_match = re.search(r'time=["\'„“]([^"\'„“\-]+)', line)
                            
                            timestamp = f"{date_match.group(1) if date_match else ''} {time_match.group(1) if time_match else ''}".strip()
                            details = msg
                            
                            conn_match = re.search(r'Connect from ([\w:]+) to ([\w:]+)', msg, re.IGNORECASE)
                            if conn_match:
                                source, dest, status = conn_match.group(1), conn_match.group(2), "Success"
                            
                            if any(err in msg.lower() for err in ["error", "reject", "fail", "timeout"]): status = "Error"

                        # Format 2: Standard Postfix/SMTP
                        elif "postfix" in line.lower() or "smtpd" in line.lower():
                            time_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                            timestamp = time_match.group(1) if time_match else "Unknown"
                            
                            sender = re.search(r'from=<([^>]+)>', line)
                            recipient = re.search(r'to\s*=?\s*<([^>]+)>', line)
                            source = sender.group(1) if sender else "N/A"
                            dest = recipient.group(1) if recipient else "N/A"

                            ip_match = re.search(self.ip_pattern, line)
                            if ip_match and source == "N/A": source = ip_match.group(0)

                            if any(w in line.lower() for w in ["reject:", "bounced", "failed"]): status = "Error"
                            elif "status=sent" in line.lower(): status = "Success"

                        self.parsed_data.append((timestamp, status, source, dest, details))
            except Exception as e:
                print(f"Error parsing file: {e}")

        self.apply_filters()
        messagebox.showinfo("Success", f"Loaded {len(self.parsed_data)} records successfully.")

    def apply_filters(self, *args):
        query = self.search_var.get().lower()
        status_filter = self.status_var.get()

        self.filtered_data = []
        for row in self.parsed_data:
            # 1. Apply Status Filter
            if status_filter != "All Status" and row[1] != status_filter:
                continue
            
            # 2. Apply Text Filter (Search in IP, Email, and Details)
            if query and not (query in row[2].lower() or query in row[3].lower() or query in row[4].lower()):
                continue
                
            self.filtered_data.append(row)

        self.update_treeview()
        self.update_stats()

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        self.row_details_map.clear()
        
        for row in self.filtered_data:
            item_id = self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3]), tags=(row[1],))
            self.row_details_map[item_id] = row

    def update_stats(self):
        success = sum(1 for row in self.filtered_data if row[1] == "Success")
        error = sum(1 for row in self.filtered_data if row[1] == "Error")
        info = sum(1 for row in self.filtered_data if row[1] == "Info")

        self.lbl_total.configure(text=f"Total Displayed: {len(self.filtered_data)}")
        self.lbl_success.configure(text=f"Success/Sent: {success}")
        self.lbl_error.configure(text=f"Errors/Rejected: {error}")
        self.lbl_info.configure(text=f"Information: {info}")

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        full_row = self.row_details_map.get(selected[0])
        if not full_row: return

        details = full_row[4]
        source = full_row[2]

        # --- Highlight Text in Details Box ---
        self.details_box.delete("1.0", "end")
        self.details_box.insert("end", details)
        
        # Highlight IPs
        for match in re.finditer(self.ip_pattern, details):
            self.details_box.tag_add("ip_highlight", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
            
        # Highlight Emails
        for match in re.finditer(self.email_pattern, details):
            self.details_box.tag_add("email_highlight", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        # --- Intelligent Geolocation (IP or Domain) ---
        self.geo_label.configure(text="Analyzing Target for Geolocation...")
        threading.Thread(target=self.resolve_and_locate, args=(source, details)).start()

    def resolve_and_locate(self, source, details):
        target_ip = None
        target_name = "Unknown"

        # 1. Check if source is directly an IP
        if re.match(self.ip_pattern, source):
            target_ip = source
            target_name = f"IP: {source}"
        # 2. Check if source is an Email (Resolve Domain to IP)
        elif "@" in source:
            domain = source.split("@")[1]
            target_name = f"Domain: {domain}"
            try:
                target_ip = socket.gethostbyname(domain)
            except socket.gaierror:
                target_ip = None
        # 3. Fallback: Find any IP in the details string
        else:
            ip_matches = re.findall(self.ip_pattern, details)
            if ip_matches:
                target_ip = ip_matches[0]
                target_name = f"Found IP: {target_ip}"

        # Geolocation Process
        if not target_ip:
            self.after(0, lambda: self.update_map("No valid IP or Domain to locate", 0, 0, 1))
            return

        if target_ip.startswith(("127.", "192.168.", "10.", "172.", "::1")):
            self.after(0, lambda: self.update_map(f"{target_name} (Local/Private Network)", 0, 0, 1))
            return

        try:
            res = requests.get(f"http://ip-api.com/json/{target_ip}").json()
            if res.get("status") == "success":
                lat, lon = res.get("lat"), res.get("lon")
                info_str = f"{target_name}\nLocation: {res.get('city')}, {res.get('country')}\nISP: {res.get('isp')}"
                self.after(0, lambda: self.update_map(info_str, lat, lon, 8))
            else:
                self.after(0, lambda: self.update_map(f"Could not locate: {target_name}", 0, 0, 1))
        except Exception:
            self.after(0, lambda: self.geo_label.configure(text="Network API Error"))

    def update_map(self, label_text, lat, lon, zoom):
        self.geo_label.configure(text=label_text)
        if lat != 0 and lon != 0:
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(zoom)
            self.map_widget.set_marker(lat, lon, text=label_text.split("\n")[0]) # Marker takes the short name
        else:
            self.map_widget.set_position(0, 0)
            self.map_widget.set_zoom(1)
            self.map_widget.delete_all_marker()

    def export_txt(self):
        if not self.filtered_data: return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")], title="Export as TXT")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    for row in self.filtered_data:
                        f.write(f"[{row[0]}] [{row[1]}] From: {row[2]} -> To: {row[3]}\n")
                        f.write(f"DETAILS: {row[4]}\n")
                        f.write("-" * 80 + "\n")
                messagebox.showinfo("Success", "Data exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = UltimateLogAnalyzer()
    app.mainloop()
