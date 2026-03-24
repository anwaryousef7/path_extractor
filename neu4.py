import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import re
import os
import requests
import threading
import tkintermapview

# Set UI Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AdvancedGeoAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LogMaster Pro - Geo & IP Analyzer")
        self.geometry("1400x950")
        self.minsize(1200, 800)

        self.parsed_data = []
        self.filtered_data = []
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_frame, text="LogMaster Pro", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        ctk.CTkButton(self.sidebar_frame, text="Load Logs", command=self.load_files, height=40).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.sidebar_frame, text="Export TXT", command=self.export_txt, height=40, fg_color="#8E44AD", hover_color="#732D91").pack(pady=10, padx=20, fill="x")

        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_frame.grid_rowconfigure(1, weight=1) # Treeview takes upper half
        self.main_frame.grid_rowconfigure(2, weight=1) # Details & Map takes lower half
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 1. Top Filter Bar
        self.filter_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.apply_filters)
        ctk.CTkEntry(self.filter_frame, placeholder_text="Search Details, IP, Sender...", textvariable=self.search_var, width=350).pack(side="left", padx=10, pady=10)

        # 2. Treeview (Table)
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        columns = ("Timestamp", "Status", "Source", "Destination")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="#e0e0e0", rowheight=30, fieldbackground="#2b2b2b")
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

        self.tree.tag_configure('Success', foreground='#4CAF50')
        self.tree.tag_configure('Error', foreground='#F44336')

        for col in columns: self.tree.heading(col, text=col)
        self.tree.column("Timestamp", width=150); self.tree.column("Status", width=100)
        self.tree.column("Source", width=250); self.tree.column("Destination", width=250)
        self.tree.pack(fill="both", expand=True, side="left")
        
        # Bind row selection to the Inspector Panel
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # 3. Bottom Area: Smart Inspector Panel (Text Details + Map)
        self.bottom_panel = ctk.CTkFrame(self.main_frame)
        self.bottom_panel.grid(row=2, column=0, sticky="nsew")
        self.bottom_panel.grid_columnconfigure(0, weight=2) # Details gets 2/3 width
        self.bottom_panel.grid_columnconfigure(1, weight=1) # Map gets 1/3 width

        # Left: Full Details Textbox
        self.details_frame = ctk.CTkFrame(self.bottom_panel)
        self.details_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(self.details_frame, text="Full Log Details & IP Highlighting", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.details_box = ctk.CTkTextbox(self.details_frame, font=("Consolas", 14), wrap="word")
        self.details_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Configure tags for text highlighting
        self.details_box.tag_config("ip_highlight", foreground="#F1C40F") # Yellow/Orange for IPs
        self.details_box.tag_config("error_highlight", foreground="#F44336") # Red for errors

        # Right: IP Geolocation Map
        self.geo_frame = ctk.CTkFrame(self.bottom_panel)
        self.geo_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.geo_label = ctk.CTkLabel(self.geo_frame, text="IP Geolocation Info", font=ctk.CTkFont(weight="bold"))
        self.geo_label.pack(pady=5)
        
        # Interactive Map Widget
        self.map_widget = tkintermapview.TkinterMapView(self.geo_frame, corner_radius=10)
        self.map_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.map_widget.set_position(0, 0) # Default to center of world
        self.map_widget.set_zoom(1)

    def load_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Log Files")
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
                        
                        # HAProxy / SCCM XML Format
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
                            
                            if any(err in msg.lower() for err in ["error", "reject", "fail"]): status = "Error"

                        # Postfix Format
                        elif "postfix" in line.lower() or "smtpd" in line.lower():
                            time_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                            timestamp = time_match.group(1) if time_match else "Unknown"
                            
                            sender = re.search(r'from=<([^>]+)>', line)
                            recipient = re.search(r'to\s*=?\s*<([^>]+)>', line)
                            source = sender.group(1) if sender else "N/A"
                            dest = recipient.group(1) if recipient else "N/A"

                            ip_match = re.search(r'\[([0-9a-fA-F\.\:]+)\]', line)
                            if ip_match and source == "N/A": source = ip_match.group(1)

                            if any(w in line.lower() for w in ["reject:", "bounced", "failed"]): status = "Error"
                            elif "status=sent" in line.lower(): status = "Success"

                        # Store data (Details is stored as the 5th element)
                        if status != "Info" or source != "N/A":
                            self.parsed_data.append((timestamp, status, source, dest, details))
            except Exception as e:
                print(e)

        self.apply_filters()

    def apply_filters(self, *args):
        query = self.search_var.get().lower()
        self.filtered_data = [row for row in self.parsed_data if not query or query in row[4].lower() or query in row[2].lower()]
        
        self.tree.delete(*self.tree.get_children())
        # To link Treeview item to its full details, we store the full Details in a hidden dictionary or fetch by index
        self.row_details_map = {}
        for idx, row in enumerate(self.filtered_data):
            # Display only first 4 columns in Treeview to save space
            item_id = self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3]), tags=(row[1],))
            self.row_details_map[item_id] = row # Store the full row (including details) for later retrieval

    def on_row_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        item_id = selected_items[0]
        full_row = self.row_details_map.get(item_id)
        if not full_row: return

        status, source, dest, details = full_row[1], full_row[2], full_row[3], full_row[4]

        # 1. Update Full Details Textbox & Apply Syntax Highlighting
        self.details_box.delete("1.0", "end")
        
        # Regex to find IPv4 and IPv6 addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[A-Fa-f0-9]{1,4}:){1,7}[A-Fa-f0-9]{1,4}\b'
        
        # Insert text and find matches to apply tags
        last_idx = 0
        for match in re.finditer(ip_pattern, details):
            start, end = match.span()
            self.details_box.insert("end", details[last_idx:start]) # Insert text before IP
            self.details_box.insert("end", details[start:end], "ip_highlight") # Insert IP with color tag
            last_idx = end
            
        self.details_box.insert("end", details[last_idx:]) # Insert remaining text
        
        # 2. Trigger OSINT & Map search for the Source IP
        self.geo_label.configure(text="Locating IP...")
        # Check if source is an actual IP (not an email address)
        ip_to_check = source if re.match(ip_pattern, source) else None
        
        if not ip_to_check:
            # If source is an email, try to extract IP from details
            ip_matches = re.findall(ip_pattern, details)
            if ip_matches: ip_to_check = ip_matches[0]

        if ip_to_check:
            threading.Thread(target=self.fetch_geoip, args=(ip_to_check,)).start()
        else:
            self.geo_label.configure(text="No Valid IP to Locate")
            self.map_widget.set_position(0, 0)
            self.map_widget.set_zoom(1)

    def fetch_geoip(self, ip):
        # Skip local/private IPs to save API calls
        if ip.startswith(("127.", "192.168.", "10.", "172.", "::1")):
            self.after(0, lambda: self.update_map("Local Network IP", 0, 0, 1))
            return

        try:
            res = requests.get(f"http://ip-api.com/json/{ip}").json()
            if res.get("status") == "success":
                lat, lon = res.get("lat"), res.get("lon")
                info = f"IP: {ip} | {res.get('city')}, {res.get('country')} | ISP: {res.get('isp')}"
                self.after(0, lambda: self.update_map(info, lat, lon, 10))
            else:
                self.after(0, lambda: self.update_map(f"Could not locate IP: {ip}", 0, 0, 1))
        except:
            self.after(0, lambda: self.geo_label.configure(text="Network Error locating IP"))

    def update_map(self, label_text, lat, lon, zoom):
        self.geo_label.configure(text=label_text)
        if lat != 0 and lon != 0:
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(zoom)
            self.map_widget.set_marker(lat, lon, text=label_text.split("|")[0].strip())
        else:
            self.map_widget.set_position(0, 0)
            self.map_widget.set_zoom(1)
            self.map_widget.delete_all_marker()

    def export_txt(self):
        # Export logic...
        pass

if __name__ == "__main__":
    app = AdvancedGeoAnalyzer()
    app.mainloop()
