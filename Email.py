import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import re

# Set the appearance mode and default color theme
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class EmailLogAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("Email Log Analyzer & Visualizer")
        self.geometry("950x650")
        self.minsize(800, 500)

        # Data storage
        self.log_data = []

        # Build the User Interface
        self.setup_ui()

    def setup_ui(self):
        # --- Top Frame: Controls ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=20, padx=20, fill="x")

        self.load_btn = ctk.CTkButton(self.top_frame, text="Load Log File", 
                                      command=self.load_file, font=("Arial", 14, "bold"))
        self.load_btn.pack(side="left", padx=10)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Search by email...", 
                                         textvariable=self.search_var, width=250)
        self.search_entry.pack(side="left", padx=10)

        self.search_btn = ctk.CTkButton(self.top_frame, text="Search", 
                                        command=self.filter_data, fg_color="#2FA572", hover_color="#1D7A50")
        self.search_btn.pack(side="left", padx=10)

        self.reset_btn = ctk.CTkButton(self.top_frame, text="Reset", 
                                       command=self.reset_filter, fg_color="#5C5C5C", hover_color="#3B3B3B")
        self.reset_btn.pack(side="left", padx=10)

        # --- Middle Frame: Summary Statistics ---
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(pady=10, padx=20, fill="x")

        self.total_label = ctk.CTkLabel(self.stats_frame, text="Total Logs: 0", font=("Arial", 14, "bold"))
        self.total_label.pack(side="left", padx=20, pady=15)

        self.sent_label = ctk.CTkLabel(self.stats_frame, text="Sent/Delivered: 0", 
                                       text_color="#2FA572", font=("Arial", 14, "bold"))
        self.sent_label.pack(side="left", padx=20, pady=15)

        self.bounced_label = ctk.CTkLabel(self.stats_frame, text="Bounced/Failed: 0", 
                                          text_color="#FF4C4C", font=("Arial", 14, "bold"))
        self.bounced_label.pack(side="left", padx=20, pady=15)

        # --- Bottom Frame: Data Table ---
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Treeview (Table) setup
        columns = ("Date & Time", "Sender (From)", "Recipient (To)", "Status")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")

        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        
        # Adjust specific column widths
        self.tree.column("Date & Time", width=150)
        self.tree.column("Sender (From)", width=250)
        self.tree.column("Recipient (To)", width=250)
        self.tree.column("Status", width=100)

        # Style the Treeview to match the dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        rowheight=30, 
                        fieldbackground="#2b2b2b",
                        font=("Arial", 11))
        style.configure("Treeview.Heading", 
                        background="#1f1f1f", 
                        foreground="white", 
                        font=('Arial', 12, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

        self.tree.pack(fill="both", expand=True, side="left", padx=(10, 0), pady=10)

        # Scrollbar for the table
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Email Log File",
            filetypes=[("Text Files", "*.txt"), ("Log Files", "*.log"), ("All Files", "*.*")]
        )
        if filepath:
            self.parse_log_file(filepath)

    def parse_log_file(self, filepath):
        self.log_data = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    # Regex to extract Date, Emails, and Status. 
                    # NOTE: Adjust these regex patterns based on the exact format of your provider's logs.
                    
                    # Look for date patterns like YYYY-MM-DD HH:MM:SS or similar
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', line)
                    # Look for email addresses
                    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                    # Look for status keywords
                    status_match = re.search(r'(?i)\b(sent|delivered|bounced|failed|deferred|rejected|blocked)\b', line)

                    date = date_match.group(0) if date_match else "N/A"
                    sender = email_matches[0] if len(email_matches) > 0 else "N/A"
                    recipient = email_matches[1] if len(email_matches) > 1 else "N/A"
                    status = status_match.group(0).capitalize() if status_match else "Unknown"

                    # Add to data only if at least one email is found (to filter out random log noises)
                    if sender != "N/A" or recipient != "N/A":
                        self.log_data.append((date, sender, recipient, status))

            self.populate_table(self.log_data)
            self.update_statistics(self.log_data)
            messagebox.showinfo("Success", f"Successfully parsed {len(self.log_data)} email records.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{str(e)}")

    def populate_table(self, data):
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert new rows
        for row in data:
            self.tree.insert("", "end", values=row)

    def update_statistics(self, data):
        total = len(data)
        sent = sum(1 for row in data if row[3] in ["Sent", "Delivered"])
        bounced = sum(1 for row in data if row[3] in ["Bounced", "Failed", "Rejected", "Blocked"])

        self.total_label.configure(text=f"Total Logs: {total}")
        self.sent_label.configure(text=f"Sent/Delivered: {sent}")
        self.bounced_label.configure(text=f"Bounced/Failed: {bounced}")

    def filter_data(self):
        query = self.search_var.get().lower()
        if not query:
            self.reset_filter()
            return

        filtered_data = [row for row in self.log_data if query in row[1].lower() or query in row[2].lower()]
        self.populate_table(filtered_data)
        self.update_statistics(filtered_data)

    def reset_filter(self):
        self.search_var.set("")
        self.populate_table(self.log_data)
        self.update_statistics(self.log_data)


if __name__ == "__main__":
    app = EmailLogAnalyzerApp()
    app.mainloop()
