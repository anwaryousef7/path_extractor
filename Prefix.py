import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import re
import csv
import os

# Set UI Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AdvancedEmailAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Main Window Config
        self.title("Postfix Email Log Analyzer Pro")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        self.parsed_data = []

        self.setup_ui()

    def setup_ui(self):
        # --- Grid Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Left) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        logo_label = ctk.CTkLabel(self.sidebar_frame, text="Log Analyzer Pro", font=ctk.CTkFont(size=24, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="Load Postfix Log", command=self.load_file, height=40)
        self.load_btn.grid(row=1, column=0, padx=20, pady=10)

        self.export_btn = ctk.CTkButton(self.sidebar_frame, text="Export to CSV", command=self.export_csv, height=40, fg_color="#2FA572", hover_color="#1D7A50")
        self.export_btn.grid(row=2, column=0, padx=20, pady=10)

        # Dashboard Stats in Sidebar
        self.stats_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, padx=20, pady=30, sticky="w")
        
        self.lbl_total = ctk.CTkLabel(self.stats_frame, text="Total: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_total.pack(anchor="w", pady=5)
        
        self.lbl_sent = ctk.CTkLabel(self.stats_frame, text="Sent: 0", text_color="#2FA572", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_sent.pack(anchor="w", pady=5)
        
        self.lbl_rejected = ctk.CTkLabel(self.stats_frame, text="Rejected: 0", text_color="#FF4C4C", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_rejected.pack(anchor="w", pady=5)
        
        self.lbl_deferred = ctk.CTkLabel(self.stats_frame, text="Deferred: 0", text_color="#F5A623", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_deferred.pack(anchor="w", pady=5)

        # --- Main Content (Right) ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Filters Bar
        self.filter_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Search Email or IP...", textvariable=self.search_var, width=300, height=35)
        self.search_entry.pack(side="left", padx=15, pady=15)

        self.status_var = ctk.StringVar(value="All Status")
        self.status_dropdown = ctk.CTkOptionMenu(self.filter_frame, variable=self.status_var, values=["All Status", "Sent", "Rejected", "Deferred", "Bounced"], width=150, height=35, command=self.apply_filters)
        self.status_dropdown.pack(side="left", padx=15, pady=15)

        self.search_btn = ctk.CTkButton(self.filter_frame, text="Apply Filters", command=self.apply_filters, width=120, height=35)
        self.search_btn.pack(side="left", padx=15, pady=15)

        # Table (Treeview)
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("Timestamp", "Status", "Sender", "Recipient", "Client IP", "Reason/Details")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="extended")

        # Treeview Styling
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#242424", foreground="#e0e0e0", rowheight=35, fieldbackground="#242424", borderwidth=0, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=('Segoe UI', 11, 'bold'), borderwidth=0, padding=5)
        style.map('Treeview', background=[('selected', '#1f538d')])

        # Column configuration
        self.tree.heading("Timestamp", text="Time/Date")
        self.tree.column("Timestamp", width=120, anchor="w")
        
        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=90, anchor="center")
        
        self.tree.heading("Sender", text="Sender (From)")
        self.tree.column("Sender", width=200, anchor="w")
        
        self.tree.heading("Recipient", text="Recipient (To)")
        self.tree.column("Recipient", width=200, anchor="w")
        
        self.tree.heading("Client IP", text="Server IP")
        self.tree.column("Client IP", width=120, anchor="center")
        
        self.tree.heading("Reason/Details", text="Reason / Log Details")
        self.tree.column("Reason/Details", width=400, anchor="w")

        self.tree.pack(fill="both", expand=True, side="left", padx=5, pady=5)

        # Scrollbars
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        
        x_scroll = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=x_scroll.set)
        x_scroll.grid(row=2, column=0, sticky="ew")

    def load_file(self):
        filepath = filedialog.askopenfilename(title="Select Postfix Log", filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All", "*.*")])
        if not filepath:
            return
            
        self.parse_postfix_log(filepath)

    def parse_postfix_log(self, filepath):
        self.parsed_data = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    # 1. Extract Timestamp (Standard Syslog format e.g., "Mar 24 11:01:15" or ISO)
                    time_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                    timestamp = time_match.group(1) if time_match else "Unknown Time"

                    # 2. Extract Sender (from=<...>)
                    sender_match = re.search(r'from=<([^>]+)>', line)
                    sender = sender_match.group(1) if sender_match else ""

                    # 3. Extract Recipient (to=<...> or to <...>)
                    recipient_match = re.search(r'to\s*=?\s*<([^>]+)>', line)
                    recipient = recipient_match.group(1) if recipient_match else ""

                    # 4. Extract IP Address (e.g., from server.com[192.168.1.1])
                    ip_match = re.search(r'\[([0-9\.]+)\]', line)
                    client_ip = ip_match.group(1) if ip_match else "Local/Unknown"

                    # 5. Determine Status and Extract Reason
                    status = "Unknown"
                    reason = ""
                    
                    line_lower = line.lower()
                    
                    if "reject:" in line_lower:
                        status = "Rejected"
                        # Extract the reason between the IP and the 'from=' part
                        reason_match = re.search(r'reject:[^\[]+\[[^\]]+\]:\s*(.*?)(?:;\s*from=|$)', line)
                        reason = reason_match.group(1).strip() if reason_match else "Rejected by server rules"
                        
                    elif "status=sent" in line_lower:
                        status = "Sent"
                        reason_match = re.search(r'status=sent\s*\((.*?)\)', line)
                        reason = reason_match.group(1).strip() if reason_match else "Delivered successfully"
                        
                    elif "status=deferred" in line_lower:
                        status = "Deferred"
                        reason_match = re.search(r'status=deferred\s*\((.*?)\)', line)
                        reason = reason_match.group(1).strip() if reason_match else "Delivery delayed"
                        
                    elif "status=bounced" in line_lower:
                        status = "Bounced"
                        reason_match = re.search(r'status=bounced\s*\((.*?)\)', line)
                        reason = reason_match.group(1).strip() if reason_match else "Message bounced"
                    
                    # Only add lines that have a clear email action to avoid system noise
                    if sender or recipient or status != "Unknown":
                        if not sender: sender = "N/A"
                        if not recipient: recipient = "N/A"
                        if not reason: reason = line.strip()[-60:] + "..." # Fallback to end of line
                        
                        self.parsed_data.append((timestamp, status, sender, recipient, client_ip, reason))

            self.apply_filters()
            messagebox.showinfo("Success", f"Analyzed {len(self.parsed_data)} email transactions successfully.")

        except Exception as e:
            messagebox.showerror("Parsing Error", f"An error occurred while reading the file:\n{e}")

    def apply_filters(self, *args):
        query = self.search_var.get().lower()
        status_filter = self.status_var.get()

        filtered = []
        for row in self.parsed_data:
            # Check Status
            if status_filter != "All Status" and row[1] != status_filter:
                continue
            
            # Check Search Query (Search in Sender, Recipient, or IP)
            if query and not (query in row[2].lower() or query in row[3].lower() or query in row[4].lower()):
                continue
            
            filtered.append(row)

        self.populate_table(filtered)
        self.update_stats(filtered)

    def populate_table(self, data):
        self.tree.delete(*self.tree.get_children())
        for row in data:
            self.tree.insert("", "end", values=row)

    def update_stats(self, data):
        total = len(data)
        sent = sum(1 for row in data if row[1] == "Sent")
        rejected = sum(1 for row in data if row[1] == "Rejected" or row[1] == "Bounced")
        deferred = sum(1 for row in data if row[1] == "Deferred")

        self.lbl_total.configure(text=f"Total Records: {total}")
        self.lbl_sent.configure(text=f"Sent/Delivered: {sent}")
        self.lbl_rejected.configure(text=f"Rejected/Bounced: {rejected}")
        self.lbl_deferred.configure(text=f"Deferred: {deferred}")

    def export_csv(self):
        if not self.parsed_data:
            messagebox.showwarning("Empty", "No data to export. Please load a log file first.")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")], title="Save Output as CSV")
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "Status", "Sender", "Recipient", "Client IP", "Reason/Details"])
                    
                    # Export currently filtered data from the Treeview
                    for child in self.tree.get_children():
                        writer.writerow(self.tree.item(child)["values"])
                        
                messagebox.showinfo("Export Successful", f"Data exported to {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not save file:\n{e}")

if __name__ == "__main__":
    app = AdvancedEmailAnalyzer()
    app.mainloop()
