import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import re
import csv
import os
import requests
from fpdf import FPDF
import threading
import webbrowser
from pyvis.network import Network
from collections import defaultdict

# Set UI Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UltimateThreatAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ultimate Postfix OSINT & Network Analyzer")
        self.geometry("1400x900")
        self.minsize(1200, 700)

        self.parsed_data = []
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="Threat Intel Pro", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))

        # Core Actions
        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="1. Load Postfix Log", command=self.load_file, height=40)
        self.load_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Advanced Analysis Buttons
        self.insight_btn = ctk.CTkButton(self.sidebar_frame, text="2. Generate Contextual Insights", command=self.generate_insights, height=40, fg_color="#8E44AD", hover_color="#732D91")
        self.insight_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.network_btn = ctk.CTkButton(self.sidebar_frame, text="3. Link Analysis (Network Graph)", command=self.generate_network_graph, height=40, fg_color="#D35400", hover_color="#A04000")
        self.network_btn.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Exports
        self.export_csv_btn = ctk.CTkButton(self.sidebar_frame, text="Export Data (CSV)", command=self.export_csv, fg_color="#2FA572", hover_color="#1D7A50")
        self.export_csv_btn.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.export_pdf_btn = ctk.CTkButton(self.sidebar_frame, text="Export Report (PDF)", command=self.export_pdf, fg_color="#C0392B", hover_color="#922B21")
        self.export_pdf_btn.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Dashboard Stats
        self.stats_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.stats_frame.grid(row=6, column=0, padx=20, pady=20, sticky="w")
        
        self.lbl_total = ctk.CTkLabel(self.stats_frame, text="Total Logs: 0", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_total.pack(anchor="w", pady=2)
        
        self.lbl_rejected = ctk.CTkLabel(self.stats_frame, text="Rejected: 0", text_color="#FF4C4C", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_rejected.pack(anchor="w", pady=2)

        # OSINT Panel
        self.osint_frame = ctk.CTkFrame(self.sidebar_frame)
        self.osint_frame.grid(row=7, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.osint_frame, text="OSINT IP Checker", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.investigate_btn = ctk.CTkButton(self.osint_frame, text="Investigate Selected IP", command=self.investigate_ip)
        self.investigate_btn.pack(pady=5, padx=10, fill="x")
        
        self.osint_result = ctk.CTkTextbox(self.osint_frame, height=120, wrap="word", font=("Consolas", 11))
        self.osint_result.pack(pady=5, padx=10, fill="x")

        # --- Main Content ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # AI Insights Textbox (Hidden by default, shown when insights are generated)
        self.insights_textbox = ctk.CTkTextbox(self.main_frame, height=150, wrap="word", font=("Consolas", 12), text_color="#F1C40F")
        self.insights_textbox.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.insights_textbox.insert("1.0", "--- Contextual AI Insights will appear here ---\nClick 'Generate Contextual Insights' to analyze the loaded data.")

        # Table (Treeview)
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("Timestamp", "Status", "Sender", "Domain", "Recipient", "IP Address", "Details")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#242424", foreground="#e0e0e0", rowheight=30, fieldbackground="#242424")
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.column("Timestamp", width=120)
        self.tree.column("Status", width=80, anchor="center")
        self.tree.column("Sender", width=180)
        self.tree.column("Domain", width=120)
        self.tree.column("Recipient", width=180)
        self.tree.column("IP Address", width=110, anchor="center")
        self.tree.column("Details", width=350)

        self.tree.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")

    def load_file(self):
        filepath = filedialog.askopenfilename(title="Select Log File")
        if filepath:
            self.parse_log(filepath)

    def parse_log(self, filepath):
        self.parsed_data = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    time_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                    timestamp = time_match.group(1) if time_match else "Unknown"

                    sender_match = re.search(r'from=<([^>]+)>', line)
                    sender = sender_match.group(1) if sender_match else "N/A"
                    domain = sender.split('@')[1] if '@' in sender else "N/A"

                    recipient_match = re.search(r'to\s*=?\s*<([^>]+)>', line)
                    recipient = recipient_match.group(1) if recipient_match else "N/A"

                    ip_match = re.search(r'\[([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\]', line)
                    client_ip = ip_match.group(1) if ip_match else "N/A"

                    status = "Unknown"
                    reason = ""
                    
                    if "reject:" in line.lower():
                        status = "Rejected"
                        reason_match = re.search(r'reject:[^\[]+\[[^\]]+\]:\s*(.*?)(?:;\s*from=|$)', line)
                        reason = reason_match.group(1).strip() if reason_match else "Rejected by server"
                    elif "status=sent" in line.lower():
                        status = "Sent"
                        reason = "Delivered successfully"
                    
                    if status != "Unknown":
                        self.parsed_data.append((timestamp, status, sender, domain, recipient, client_ip, reason))

            self.populate_table(self.parsed_data)
            self.update_stats(self.parsed_data)
            messagebox.showinfo("Success", f"Loaded {len(self.parsed_data)} records.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def populate_table(self, data):
        self.tree.delete(*self.tree.get_children())
        for row in data:
            self.tree.insert("", "end", values=row)

    def update_stats(self, data):
        total = len(data)
        rejected = sum(1 for row in data if row[1] == "Rejected")
        self.lbl_total.configure(text=f"Total Records: {total}")
        self.lbl_rejected.configure(text=f"Rejected/Failed: {rejected}")

    # --- Feature 1: Contextual Interpretation (Heuristics Engine) ---
    def generate_insights(self):
        if not self.parsed_data:
            messagebox.showwarning("Warning", "Please load data first.")
            return

        self.insights_textbox.delete("1.0", "end")
        insights = "[+] Automated Security Context Analysis Started...\n\n"

        # Dictionaries for statistical correlation
        ip_behavior = defaultdict(lambda: {'total': 0, 'rejected': 0, 'targets': set()})
        domain_behavior = defaultdict(lambda: {'total': 0, 'rejected': 0})

        for row in self.parsed_data:
            status, sender, domain, recipient, ip = row[1], row[2], row[3], row[4], row[5]
            
            if ip != "N/A":
                ip_behavior[ip]['total'] += 1
                ip_behavior[ip]['targets'].add(recipient)
                if status == "Rejected":
                    ip_behavior[ip]['rejected'] += 1
            
            if domain != "N/A":
                domain_behavior[domain]['total'] += 1
                if status == "Rejected":
                    domain_behavior[domain]['rejected'] += 1

        # Analyze IP Behavior (Looking for Spammers / Brute-force)
        insights += "--- IP Address Threat Intelligence ---\n"
        threat_found = False
        for ip, stats in ip_behavior.items():
            reject_rate = (stats['rejected'] / stats['total']) * 100
            
            # Context 1: High Rejection Rate from single IP
            if stats['total'] > 5 and reject_rate > 70:
                threat_found = True
                insights += f"[CRITICAL] IP {ip}: High rejection rate ({reject_rate:.1f}%). {stats['rejected']}/{stats['total']} attempts blocked.\n"
                insights += "   -> Interpretation: Highly likely to be a compromised server, Spam bot, or performing a Brute-Force attack.\n"
            
            # Context 2: Directory Harvest Attack (DHA)
            if stats['total'] > 10 and len(stats['targets']) > 10 and reject_rate > 50:
                threat_found = True
                insights += f"[WARNING] IP {ip}: Attempted to email {len(stats['targets'])} unique recipients with high failure rate.\n"
                insights += "   -> Interpretation: Possible Directory Harvest Attack (DHA) trying to guess valid internal email addresses.\n"

        if not threat_found:
            insights += "[INFO] No critical IP threats detected based on current heuristics.\n"

        # Analyze Domain Behavior (Looking for Spoofing / Blacklisted Domains)
        insights += "\n--- Domain Reputation Context ---\n"
        domain_threat = False
        for domain, stats in domain_behavior.items():
            if stats['total'] > 5 and (stats['rejected'] / stats['total']) > 0.8:
                domain_threat = True
                insights += f"[WARNING] Domain '{domain}': 80%+ of emails from this domain were rejected.\n"
                insights += "   -> Interpretation: Domain might lack SPF/DKIM records, is blacklisted, or is being spoofed by an attacker.\n"
                
        if not domain_threat:
            insights += "[INFO] No heavily rejected domains detected.\n"

        self.insights_textbox.insert("1.0", insights)

    # --- Feature 2: Link & Network Analysis (Graph Visualization) ---
    def generate_network_graph(self):
        if not self.parsed_data:
            messagebox.showwarning("Warning", "Please load data first.")
            return

        try:
            # Create a PyVis network
            net = Network(height='100vh', width='100%', bgcolor='#1a1a1a', font_color='white', directed=True)
            net.force_atlas_2based() # Physics engine for beautiful layout

            nodes_added = set()

            for row in self.parsed_data:
                status, sender, recipient, ip = row[1], row[2], row[4], row[5]

                # Edge Colors based on Status
                edge_color = '#4CAF50' if status == "Sent" else '#F44336' # Green for sent, Red for rejected

                # Add IP Node
                if ip != "N/A" and ip not in nodes_added:
                    net.add_node(ip, label=ip, title="Connecting Server IP", color='#E67E22', size=25, shape='hexagon')
                    nodes_added.add(ip)

                # Add Sender Node
                if sender != "N/A" and sender not in nodes_added:
                    net.add_node(sender, label=sender, title="Sender Address", color='#3498DB', size=20)
                    nodes_added.add(sender)

                # Add Recipient Node
                if recipient != "N/A" and recipient not in nodes_added:
                    net.add_node(recipient, label=recipient, title="Target Recipient", color='#9B59B6', size=20)
                    nodes_added.add(recipient)

                # Create Links (Relationships)
                if ip != "N/A" and sender != "N/A":
                    net.add_edge(ip, sender, color=edge_color, title=f"Originated from IP ({status})")
                
                if sender != "N/A" and recipient != "N/A":
                    net.add_edge(sender, recipient, color=edge_color, title=f"Emailed to ({status})")

            # Save and open the graph
            graph_path = os.path.abspath("network_analysis.html")
            net.write_html(graph_path)
            webbrowser.open(f"file://{graph_path}")
            
        except Exception as e:
            messagebox.showerror("Graph Error", f"Could not generate network graph:\n{e}")

    # --- Feature 3: OSINT ---
    def investigate_ip(self):
        selected = self.tree.selection()
        if not selected: return messagebox.showwarning("Warning", "Select a row first.")
        ip = self.tree.item(selected)["values"][5]
        if ip in ("N/A", "Unknown") or ip.startswith(("127.", "192.168.", "10.")):
            self.osint_result.delete("1.0", "end")
            self.osint_result.insert("1.0", f"IP {ip} is Local/Invalid for OSINT.")
            return

        self.osint_result.delete("1.0", "end")
        self.osint_result.insert("1.0", f"Querying {ip}...\n")
        threading.Thread(target=self.fetch_osint, args=(ip,)).start()

    def fetch_osint(self, ip):
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,isp,proxy,hosting", timeout=5).json()
            if res.get("status") == "success":
                proxy_status = "DETECTED" if res.get("proxy") or res.get("hosting") else "Clear"
                text = f"IP: {ip}\nCountry: {res.get('country')}\nISP: {res.get('isp')}\nVPN/Datacenter: {proxy_status}"
            else:
                text = "OSINT API failed to find data."
            self.after(0, lambda: self.osint_result.delete("1.0", "end") or self.osint_result.insert("1.0", text))
        except Exception as e:
            self.after(0, lambda: self.osint_result.insert("end", f"\nError: {e}"))

    # --- Exports ---
    def export_csv(self):
        if not self.parsed_data: return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if filepath:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Status", "Sender", "Domain", "Recipient", "IP", "Details"])
                for child in self.tree.get_children():
                    writer.writerow(self.tree.item(child)["values"])
            messagebox.showinfo("Success", "CSV Exported!")

    def export_pdf(self):
        if not self.parsed_data: return
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")])
        if not filepath: return
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, txt="Advanced Email Threat Report", ln=True, align='C')
            pdf.ln(5)
            
            pdf.set_font("Arial", "B", 10)
            pdf.cell(30, 8, "Timestamp", 1)
            pdf.cell(20, 8, "Status", 1)
            pdf.cell(50, 8, "Sender", 1)
            pdf.cell(30, 8, "IP Address", 1)
            pdf.cell(60, 8, "Details (Truncated)", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 8)
            for child in self.tree.get_children():
                row = self.tree.item(child)["values"]
                pdf.cell(30, 8, str(row[0])[:15], 1)
                pdf.cell(20, 8, str(row[1]), 1)
                pdf.cell(50, 8, str(row[2])[:30], 1)
                pdf.cell(30, 8, str(row[5]), 1)
                pdf.cell(60, 8, str(row[6])[:40], 1)
                pdf.ln()
            pdf.output(filepath)
            messagebox.showinfo("Success", "PDF Generated!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = UltimateThreatAnalyzer()
    app.mainloop()
