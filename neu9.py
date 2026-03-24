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

        self.title("LogMaster Pro - AI Parsing Edition")
        self.geometry("1450x950")
        self.minsize(1200, 800)

        self.parsed_data = []
        self.filtered_data = []
        self.row_details_map = {}
        self.unique_entities = set()
        
        # [UPDATED] Super Robust Regex Patterns
        # This IPv6 pattern handles double colons `::` and complex hex naturally
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[a-fA-F0-9]*:){2,}[a-fA-F0-9:]+\b'
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

        # Stats
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

        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_frame.grid_rowconfigure(1, weight=1) 
        self.main_frame.grid_rowconfigure(2, weight=1) 
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Filter Bar
        self.filter_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Text Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.apply_filters)
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Live Search...", textvariable=self.search_var, width=220, height=35)
        self.search_entry.pack(side="left", padx=10, pady=15)

        # Entity Dropdown Filter (IP, Email, Domain)
        self.entity_var = ctk.StringVar(value="All Entities")
        self.entity_combo = ctk.CTkComboBox(self.filter_frame, variable=self.entity_var, values=["All Entities"], width=280, height=35, command=self.apply_filters)
        self.entity_combo.pack(side="left", padx=10, pady=15)
        self.entity_combo.set("All Entities")

        # Status Dropdown
        self.status_var = ctk.StringVar(value="All Status")
        self.status_menu = ctk.CTkOptionMenu(self.filter_frame, variable=self.status_var, values=["All Status", "Success", "Error", "Info"], command=self.apply_filters, width=120, height=35)
        self.status_menu.pack(side="left", padx=10, pady=15)

        # Treeview (Table)
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

        # Bottom Panel (Details & Map)
        self.bottom_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_panel.grid(row=2, column=0, sticky="nsew")
        self.bottom_panel.grid_columnconfigure(0, weight=3)
        self.bottom_panel.grid_columnconfigure(1, weight=2)

        # Details Textbox
        self.details_frame = ctk.CTkFrame(self.bottom_panel)
        self.details_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(self.details_frame, text="Contextual Log Details (IP & Email Highlighted)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.details_box = ctk.CTkTextbox(self.details_frame, font=("Consolas", 14), wrap="word", spacing1=2, spacing3=2)
        self.details_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.details_box.tag_config("ip_highlight", foreground="#F39C12")
        self.details_box.tag_config("email_highlight", foreground="#3498DB")

        # Map View
        self.geo_frame = ctk.CTkFrame(self.bottom_panel)
        self.geo_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.geo_label = ctk.CTkLabel(self.geo_frame, text="Geolocation Tracker", font=ctk.CTkFont(weight="bold"))
        self.geo_label.pack(pady=5)
        
        try:
            self.map_widget = tkintermapview.TkinterMapView(self.geo_frame, corner_radius=10)
            self.map_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.map_widget.set_position(0, 0)
            self.map_widget.set_zoom(1)
        except Exception as e:
            ctk.CTkLabel(self.geo_frame, text=f"Map Error: {str(e)}", text_color="red").pack()

    def add_to_entities(self, text):
        if not text or text == "N/A": return
        ip_matches = re.findall(self.ip_pattern, text)
        for ip in ip_matches: self.unique_entities.add(ip)
        
        email_matches = re.findall(self.email_pattern, text)
        for email in email_matches:
            self.unique_entities.add(email)
            domain = email.split('@')[1]
            self.unique_entities.add(domain)

    def load_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Log Files")
        if filepaths: self.parse_logs(filepaths)

    def parse_logs(self, filepaths):
        self.parsed_data.clear()
        self.unique_entities.clear()
        
        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                    for line in file:
                        try:
                            line = line.strip()
                            if not line: continue

                            timestamp, status, source, dest, details = "Unknown", "Info", "N/A", "N/A", line
                            
                            # --- AI PARSING LOGIC FOR HAProxy/SCCM ---
                            if "<![LOG[" in line:
                                # Extract Message
                                msg_match = re.search(r'<!\[LOG\[(.*?)\]\s*LOG\]!', line)
                                msg = msg_match.group(1).strip() if msg_match else "No Message"
                                
                                # Extract Date/Time safely by skipping quotes completely!
                                # Looks for 'date=' then ignores non-digits, captures digits and dashes
                                date_match = re.search(r'date=[^\d]*([\d\-]+)', line)
                                time_match = re.search(r'time=[^\d]*([\d\:\.\-]+)', line)
                                d_str = date_match.group(1) if date_match else ""
                                t_str = time_match.group(1) if time_match else ""
                                timestamp = f"{d_str} {t_str}".strip() if d_str or t_str else "Unknown"
                                
                                # Extract Component safely
                                comp_match = re.search(r'component=[^\w]*([a-zA-Z0-9_]+)', line)
                                comp = f" [Component: {comp_match.group(1)}]" if comp_match else ""
                                
                                # Setup Details
                                details = msg + comp
                                
                                # Extract IPs exactly using the words "from" and "to"
                                conn_match = re.search(r'from\s+([a-fA-F0-9\.\:]+)\s+to\s+([a-fA-F0-9\.\:]+)', msg, re.IGNORECASE)
                                if conn_match:
                                    source = conn_match.group(1)
                                    dest = conn_match.group(2)
                                    status = "Success"
                                
                                # Identify Error scenarios
                                if any(err in msg.lower() for err in ["error", "reject", "fail", "timeout", "drop"]): 
                                    status = "Error"

                            # --- Standard Postfix ---
                            elif "postfix" in line.lower() or "smtpd" in line.lower():
                                t_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                                if t_match: timestamp = t_match.group(1)
                                
                                sender = re.search(r'from=<([^>]+)>', line)
                                recipient = re.search(r'to\s*=?\s*<([^>]+)>', line)
                                if sender: source = sender.group(1)
                                if recipient: dest = recipient.group(1)

                                ip_match = re.search(self.ip_pattern, line)
                                if ip_match and source == "N/A": 
                                    source = ip_match.group(0)

                                if any(w in line.lower() for w in ["reject:", "bounced", "failed"]): status = "Error"
                                elif "status=sent" in line.lower() or "delivered" in line.lower(): status = "Success"

                            self.parsed_data.append((timestamp, status, source, dest, details))
                            
                            # Add to Dropdown Filter
                            self.add_to_entities(source)
                            self.add_to_entities(dest)
                            self.add_to_entities(details)

                        except Exception:
                            continue 
            except Exception as file_err:
                messagebox.showerror("File Error", f"Could not open file: {file_err}")

        # Populate the Dropdown Filter
        sorted_entities = ["All Entities"] + sorted(list(self.unique_entities))
        self.entity_combo.configure(values=sorted_entities)
        self.entity_combo.set("All Entities")

        self.apply_filters()
        messagebox.showinfo("Success", f"Loaded {len(self.parsed_data)} valid records.\nFound {len(self.unique_entities)} unique IPs/Emails/Domains.")

    def apply_filters(self, *args):
        query = self.search_var.get().lower()
        status_filter = self.status_var.get()
        entity_filter = self.entity_combo.get()

        self.filtered_data.clear()
        for row in self.parsed_data:
            if status_filter != "All Status" and row[1] != status_filter:
                continue
            
            if query and not (query in str(row[2]).lower() or query in str(row[3]).lower() or query in str(row[4]).lower()):
                continue
            
            if entity_filter != "All Entities":
                row_full_text = f"{row[2]} {row[3]} {row[4]}"
                if entity_filter not in row_full_text:
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

        details = str(full_row[4])
        source = str(full_row[2])

        self.details_box.delete("1.0", "end")
        self.details_box.insert("end", details)
        
        try:
            for match in re.finditer(self.ip_pattern, details):
                self.details_box.tag_add("ip_highlight", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
            for match in re.finditer(self.email_pattern, details):
                self.details_box.tag_add("email_highlight", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
        except Exception:
            pass 

        self.geo_label.configure(text="Analyzing Target for Geolocation...")
        threading.Thread(target=self.resolve_and_locate, args=(source, details), daemon=True).start()

    def resolve_and_locate(self, source, details):
        target_ip = None
        target_name = "Unknown"

        try:
            # Clean up source if it contains port like [IP]:PORT
            clean_source = source.split(']')[0].replace('[', '') if '[' in source else source
            if clean_source.count(':') > 1 and not clean_source.endswith(':'): 
                 clean_source = ':'.join(clean_source.split(':')[:-1]) if clean_source.count(':') >= 7 else clean_source

            if re.match(self.ip_pattern, clean_source) or clean_source.count(':') >= 2:
                target_ip = clean_source
                target_name = f"IP: {clean_source}"
            elif "@" in source:
                domain = source.split("@")[1]
                target_name = f"Domain: {domain}"
                try:
                    target_ip = socket.gethostbyname(domain)
                except Exception:
                    pass
            else:
                ip_matches = re.findall(self.ip_pattern, details)
                if ip_matches:
                    target_ip = ip_matches[0]
                    target_name = f"Found IP: {target_ip}"

            if not target_ip:
                self.after(0, lambda: self.update_map("No valid IP or Domain to locate", 0, 0, 1))
                return

            if target_ip.startswith(("127.", "192.168.", "10.", "172.", "::1")):
                self.after(0, lambda: self.update_map(f"{target_name} (Local Network)", 0, 0, 1))
                return

            res = requests.get(f"http://ip-api.com/json/{target_ip}", timeout=5).json()
            if res.get("status") == "success":
                lat, lon = float(res.get("lat", 0)), float(res.get("lon", 0))
                info_str = f"{target_name}\nLocation: {res.get('city', 'N/A')}, {res.get('country', 'N/A')}\nISP: {res.get('isp', 'N/A')}"
                self.after(0, lambda: self.update_map(info_str, lat, lon, 8))
            else:
                self.after(0, lambda: self.update_map(f"Could not locate: {target_name}", 0, 0, 1))
                
        except Exception:
            self.after(0, lambda: self.update_map("Network API Error or Timeout", 0, 0, 1))

    def update_map(self, label_text, lat, lon, zoom):
        try:
            self.geo_label.configure(text=label_text)
            if hasattr(self, 'map_widget'):
                if lat != 0 and lon != 0:
                    self.map_widget.set_position(lat, lon)
                    self.map_widget.set_zoom(zoom)
                    self.map_widget.delete_all_marker()
                    self.map_widget.set_marker(lat, lon, text=label_text.split("\n")[0])
                else:
                    self.map_widget.set_position(0, 0)
                    self.map_widget.set_zoom(1)
                    self.map_widget.delete_all_marker()
        except Exception:
            pass

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
                messagebox.showerror("Export Error", str(e))

if __name__ == "__main__":
    app = UltimateLogAnalyzer()
    app.mainloop()
