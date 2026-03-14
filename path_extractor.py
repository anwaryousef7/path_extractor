import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import threading
import concurrent.futures
import os
import time

# Set up the modern Light theme
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

LAYOUT = [
    ("G1", ["paths", "readable", "specific_word", "registry", "dates"]),
    ("G2", ["ipv4", "ipv6", "domain", "url", "email", "mac"]),
    ("G3", ["phone", "credit_card", "btc", "ssn", "iban"]),
    ("G4", ["md5", "sha", "base64", "hex"])
]

LANG = {
    "Deutsch": {
        "title": "PURE-DATA PURIFIER",
        "dev": "Dev: Anwar Yousef",
        "step1": "1 | QUELLDATEIEN",
        "btn_browse": "EINGABEDATEIEN AUSWÄHLEN",
        "files_selected_0": ">> 0 Dateien ausgewählt",
        "files_selected_n": ">> {} ZIELE BEREIT",
        "step2": "2 | REINIGUNGSMUSTER VIRTUELLEN",
        "keyword": "Exaktes Schlüsselwort:",
        "placeholder_kw": "z.B. passwort, admin, token...",
        "step3": "3 | EXPORTZIEL",
        "btn_output": "AUSGABEDATEI FESTLEGEN",
        "no_output": ">> Keine ausgewählt",
        "btn_start": "[ BEREINIGUNG STARTEN ]",
        "btn_processing": "[ DATEN WERDEN GEREINIGT ]",
        "status_idle": "SYSTEM BEREIT",
        "status_op": "OPERATION : {}",
        "log_title": "AKTIVITÄTSPROTOKOLL",
        "msg_req_keyword": "Bitte geben Sie ein Suchwort ein.",
        "msg_complete": "Bereinigung und Extraktion erfolgreich!",
        "msg_title_err": "Fehler erkannt",
        "msg_title_ok": "Operation abgeschlossen",
        "groups": {
            "G1": "Allgemein & System",
            "G2": "Netzwerk & Web",
            "G3": "Identität & Finanzen",
            "G4": "Krypto & Forensik"
        },
        "modes": {
            "paths": "Dateipfade (/dir/...)",
            "readable": "Reiner Text (Lesbar)",
            "specific_word": "Spezielles Wort suchen",
            "registry": "Windows Registry-Schlüssel",
            "dates": "Datum & Zeitstempel",
            "ipv4": "IPv4-Adressen",
            "ipv6": "IPv6-Adressen",
            "domain": "Domänen (google.com)",
            "url": "URLs (http/https)",
            "email": "E-Mail-Adressen",
            "mac": "MAC-Adressen",
            "phone": "Telefonnummern",
            "credit_card": "Kreditkartennummern",
            "btc": "Bitcoin-Adressen",
            "ssn": "Sozialversicherungsnummern",
            "iban": "IBAN-Kontonummern",
            "md5": "MD5-Hashes",
            "sha": "SHA-Hashes (1/256)",
            "base64": "Base64-Kodierungen (Zusatzlast)",
            "hex": "Hexadezimale Strings"
        },
        "banner": "[*] v4.0 - Advanced Purifier Engine\n[*] UX optimiert mit Registerkarten.\n[*] Entwickelt von: Anwar Yousef\n[*] Sprache: Deutsch\n[*] Status: Warte auf Dateien...\n"
    },
    "English": {
        "title": "PURE-DATA PURIFIER",
        "dev": "Dev: Anwar Yousef",
        "step1": "1 | SOURCE FILES",
        "btn_browse": "BROWSE INPUT FILES",
        "files_selected_0": ">> 0 files selected",
        "files_selected_n": ">> {} TARGET(S) LOCKED",
        "step2": "2 | CLEANING & EXTRACTION PATTERNS",
        "keyword": "Enter Exact Keyword:",
        "placeholder_kw": "e.g. password, admin, token...",
        "step3": "3 | EXPORT DESTINATION",
        "btn_output": "SET OUTPUT FILE",
        "no_output": ">> None",
        "btn_start": "[ START PURIFIER ]",
        "btn_processing": "[ CLEANING DATA ]",
        "status_idle": "SYSTEM READY",
        "status_op": "OPERATION : {}",
        "log_title": "ACTIVITY LOG",
        "msg_req_keyword": "Provide a keyword to search for.",
        "msg_complete": "Data cleaning and extraction completed successfully.",
        "msg_title_err": "Input Required",
        "msg_title_ok": "Purifier Complete",
        "groups": {
            "G1": "General & System",
            "G2": "Network & Web",
            "G3": "Identity & Finance",
            "G4": "Crypto & Forensics"
        },
        "modes": {
            "paths": "Clean File Paths (/dir/...)",
            "readable": "Extract Clean Text Only",
            "specific_word": "Specific Keyword Match",
            "registry": "Windows Registry Keys",
            "dates": "Dates & Timestamps",
            "ipv4": "IPv4 Addresses",
            "ipv6": "IPv6 Addresses",
            "domain": "Domains (e.g., google.com)",
            "url": "URLs (http/https)",
            "email": "Email Addresses",
            "mac": "MAC Addresses",
            "phone": "Phone Numbers",
            "credit_card": "Credit Card Numbers",
            "btc": "Bitcoin Addresses",
            "ssn": "Social Security Numbers",
            "iban": "IBAN Account Numbers",
            "md5": "MD5 Hashes",
            "sha": "SHA Hashes (1/256)",
            "base64": "Base64 Encoded Payloads",
            "hex": "Hexadecimal Strings"
        },
        "banner": "[*] v4.0 - Advanced Purifier Engine\n[*] UX Optimized using modern Tab Navigation.\n[*] Developed By: Anwar Yousef\n[*] Language: English\n[*] Status: Awaiting files...\n"
    }
}


class PathExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pure-Data Purifier - Developed by Anwar Yousef")
        self.geometry("1100x780")
        self.minsize(950, 700)
        
        self.files_to_process = []
        self.output_path = ""
        self.current_lang = "Deutsch"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- UI Header ---
        self.header_frame = ctk.CTkFrame(self, fg_color="#F0F0F0", corner_radius=15, height=90, border_width=1, border_color="#D0D0D0")
        self.header_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text=LANG[self.current_lang]["title"], 
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color="#1565C0" 
        )
        self.title_label.grid(row=0, column=0, sticky="sw", padx=15, pady=(15, 0))
        
        self.dev_label = ctk.CTkLabel(
            self.header_frame, 
            text=LANG[self.current_lang]["dev"], 
            font=ctk.CTkFont(family="Segoe UI", size=14, slant="italic"),
            text_color="#555555"
        )
        self.dev_label.grid(row=1, column=0, sticky="nw", padx=15, pady=(0, 15))

        self.lang_switch = ctk.CTkSegmentedButton(
            self.header_frame,
            values=["Deutsch", "English"],
            command=self.change_language,
            selected_color="#1E88E5",
            selected_hover_color="#1565C0",
            unselected_color="#E0E0E0",
            unselected_hover_color="#D0D0D0",
            text_color="#333333"
        )
        self.lang_switch.grid(row=0, column=1, rowspan=2, padx=15, pady=15, sticky="e")
        self.lang_switch.set("Deutsch")
        
        # --- Main Body ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=5)  # Controls
        self.main_frame.grid_columnconfigure(1, weight=5)  # Logs
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # === Left Panel ===
        self.left_panel = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color="#F8F8F8", border_width=1, border_color="#E0E0E0")
        self.left_panel.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        
        # SECTION 1: Inputs
        self.step1_label = ctk.CTkLabel(self.left_panel, text="1 | QUELLDATEIEN", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#666666")
        self.step1_label.pack(anchor="w", padx=15, pady=(15, 2))
        
        self.select_btn = ctk.CTkButton(
            self.left_panel, text="EINGABEDATEIEN AUSWÄHLEN", command=self.select_files, height=35,
            font=ctk.CTkFont(weight="bold", size=13), border_width=1, border_color="#1E88E5", fg_color="#FFFFFF", hover_color="#E3F2FD", text_color="#1E88E5"
        )
        self.select_btn.pack(fill="x", padx=15, pady=3)
        self.files_count_label = ctk.CTkLabel(self.left_panel, text=">> 0 Dateien ausgewählt", text_color="#707070", font=ctk.CTkFont(family="Consolas", size=12))
        self.files_count_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        # SECTION 2: Advanced Tab Navigation for Modes
        self.step2_label = ctk.CTkLabel(self.left_panel, text="2 | REINIGUNGSMUSTER VIRTUELLEN", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#666666")
        self.step2_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        self.extraction_mode_var = ctk.StringVar(value="paths")
        self.radio_buttons = {} # Store refs to update text later
        self.tab_titles = {} # Store tabs to change title later

        self.tabview = ctk.CTkTabview(
            self.left_panel, height=200, fg_color="#FFFFFF", 
            segmented_button_selected_color="#1E88E5", 
            segmented_button_unselected_color="#E3F2FD", # Light blue instead of gray
            segmented_button_unselected_hover_color="#BBDEFB",
            text_color="#1565C0" # Deep blue text for tabs
        )
        self.tabview.pack(fill="x", padx=15, pady=0)
        
        for g_id, modes in LAYOUT:
            grp_name = LANG[self.current_lang]["groups"][g_id]
            self.tabview.add(grp_name)
            self.tab_titles[g_id] = grp_name
            
            tab_frame = self.tabview.tab(grp_name)
            # Arrange radio buttons in two columns for beauty
            tab_frame.grid_columnconfigure(0, weight=1)
            tab_frame.grid_columnconfigure(1, weight=1)
            
            row = 0
            col = 0
            for mode_key in modes:
                rb = ctk.CTkRadioButton(
                    tab_frame,
                    text=LANG[self.current_lang]["modes"][mode_key],
                    variable=self.extraction_mode_var,
                    value=mode_key,
                    command=self.on_mode_change,
                    font=ctk.CTkFont(size=13, weight="bold"), # Bolder text
                    fg_color="#1E88E5", # Color when checked
                    hover_color="#1565C0", 
                    text_color="#1565C0", # Blue text to pop on white bg
                )
                rb.grid(row=row, column=col, sticky="w", padx=5, pady=5)
                self.radio_buttons[mode_key] = rb
                
                col += 1
                if col > 1:
                    col = 0
                    row += 1

        self.word_entry_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.word_entry_label = ctk.CTkLabel(self.word_entry_frame, text="Exaktes Schlüsselwort:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#E65100")
        self.word_entry_label.pack(anchor="w")
        self.word_entry = ctk.CTkEntry(self.word_entry_frame, placeholder_text="z.B. passwort, admin...", height=32, font=ctk.CTkFont(size=13), fg_color="#FFFFFF", text_color="#111111")
        self.word_entry.pack(fill="x", pady=2)
        # Entry frame hidden by default since "paths" is selected
        
        # SECTION 3: Output
        self.step3_label = ctk.CTkLabel(self.left_panel, text="3 | EXPORTZIEL", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#666666")
        self.step3_label.pack(anchor="w", padx=15, pady=(10, 2))
        
        self.output_btn = ctk.CTkButton(
            self.left_panel, text="AUSGABEDATEI FESTLEGEN", command=self.select_output, height=35,
            font=ctk.CTkFont(weight="bold", size=13), border_width=1, border_color="#E53935", fg_color="#FFFFFF", hover_color="#FFEBEE", text_color="#E53935"
        )
        self.output_btn.pack(fill="x", padx=15, pady=2)
        self.output_label = ctk.CTkLabel(self.left_panel, text=">> Keine ausgewählt", text_color="#707070", font=ctk.CTkFont(family="Consolas", size=12))
        self.output_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        ctk.CTkLabel(self.left_panel, text="").pack(expand=True)
        
        # Start Section
        self.start_btn = ctk.CTkButton(
            self.left_panel, text="[ BEREINIGUNG STARTEN ]", command=self.start_processing, height=50, 
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), fg_color="#1E88E5", hover_color="#1565C0", text_color="#FFFFFF", state="disabled", corner_radius=8
        )
        self.start_btn.pack(fill="x", padx=15, pady=(5, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.left_panel, progress_color="#43A047", fg_color="#E0E0E0", height=8)
        self.progress_bar.pack(fill="x", padx=15, pady=(5, 5))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.left_panel, text="SYSTEM BEREIT", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#1976D2")
        self.status_label.pack(anchor="center", pady=(0, 10))
        
        # === Right Panel ===
        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#D0D0D0")
        self.right_panel.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        
        self.log_header = ctk.CTkLabel(self.right_panel, text="AKTIVITÄTSPROTOKOLL", font=ctk.CTkFont(family="Consolas", size=16, weight="bold"), text_color="#333333")
        self.log_header.pack(pady=(15, 0), anchor="w", padx=20)
        
        self.log_textbox = ctk.CTkTextbox(
            self.right_panel, font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#F5F5F5", text_color="#111111", border_width=1, border_color="#E0E0E0", corner_radius=10
        )
        self.log_textbox.pack(expand=True, fill="both", padx=15, pady=(10, 15))
        self.log_textbox.insert("end", LANG[self.current_lang]["banner"])
        self.log_textbox.configure(state="disabled")

    def change_language(self, language):
        self.current_lang = language
        L = LANG[language]
        
        self.title_label.configure(text=L["title"])
        self.dev_label.configure(text=L["dev"])
        self.step1_label.configure(text=L["step1"])
        self.select_btn.configure(text=L["btn_browse"])
        
        if len(self.files_to_process) == 0:
            self.files_count_label.configure(text=L["files_selected_0"])
        else:
            self.files_count_label.configure(text=L["files_selected_n"].format(len(self.files_to_process)))
            
        self.step2_label.configure(text=L["step2"])
        
        # We must rebuild the tabs text dynamically (a bit tricky in CTkTabview) - but we can just update internal widgets
        # Updating tabview names is notoriously annoying in CTk, let's keep the backend intact and just update labels inside
        for g_id, modes in LAYOUT:
            old_name = self.tab_titles[g_id]
            new_name = L["groups"][g_id]
            # Rename tab
            if old_name != new_name:
                self.tabview.rename(old_name, new_name)
                self.tab_titles[g_id] = new_name
            
            for mode_key in modes:
                self.radio_buttons[mode_key].configure(text=L["modes"][mode_key])

        self.word_entry_label.configure(text=L["keyword"])
        self.word_entry.configure(placeholder_text=L["placeholder_kw"])
        
        self.step3_label.configure(text=L["step3"])
        self.output_btn.configure(text=L["btn_output"])
        
        if not self.output_path:
            self.output_label.configure(text=L["no_output"])
            
        if self.start_btn.cget("state") == "disabled":
            self.start_btn.configure(text=L["btn_start"])
            self.status_label.configure(text=L["status_idle"])
        else:
            self.start_btn.configure(text=L["btn_start"])
            
        self.log_header.configure(text=L["log_title"])
        self.log(L["banner"])

    def on_mode_change(self):
        val = self.extraction_mode_var.get()
        if val == "specific_word":
            self.word_entry_frame.pack(fill="x", padx=15, pady=(5, 5), after=self.tabview)
        else:
            self.word_entry_frame.pack_forget()

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def select_files(self):
        filepaths = filedialog.askopenfilenames(
            title="Select Source Files",
            filetypes=[("All Files", "*.*"), ("Text", "*.txt"), ("Log", "*.log"), ("CSV", "*.csv")]
        )
        if filepaths:
            L = LANG[self.current_lang]
            self.files_to_process = list(filepaths)
            self.files_count_label.configure(text=L["files_selected_n"].format(len(self.files_to_process)), text_color="#1E88E5")
            self.log(f"[+] -> {len(self.files_to_process)} TARGETS LOCKED.")
            self.check_ready()

    def select_output(self):
        filepath = filedialog.asksaveasfilename(
            title="Designate Export Path", 
            defaultextension=".txt", 
            filetypes=[("All Files", "*.*"), ("Text", "*.txt"), ("JSON", "*.json"), ("CSV", "*.csv")]
        )
        if filepath:
            self.output_path = filepath
            filename = os.path.basename(self.output_path)
            self.output_label.configure(text=f">> {filename}", text_color="#E53935")
            self.log(f"[+] EXPORT -> {filename}")
            self.check_ready()

    def check_ready(self):
        L = LANG[self.current_lang]
        if self.files_to_process and self.output_path:
            self.start_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="disabled")

    def process_file_task(self, file_path, mode_key, specific_word):
        results = set()
        
        patterns = {
            "paths": re.compile(r'/{1,}[a-zA-Z0-9_\-\.]+(?:/{1,}[a-zA-Z0-9_\-\.]+)*/*'),
            "readable": re.compile(r'\b[a-zA-Z]{3,}\b'),
            "ipv4": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            "ipv6": re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "url": re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'),
            "domain": re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b', re.IGNORECASE),
            "mac": re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'),
            "md5": re.compile(r'\b[a-fA-F0-9]{32}\b'),
            "sha": re.compile(r'\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b'),
            "credit_card": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
            "phone": re.compile(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
            "registry": re.compile(r'(?:HKEY_LOCAL_MACHINE|HKLM|HKEY_CURRENT_USER|HKCU|HKEY_CLASSES_ROOT|HKCR|HKEY_USERS|HKU|HKEY_CURRENT_CONFIG|HKCC)\\[a-zA-Z0-9_\\\-\s]+'),
            "dates": re.compile(r'\b\d{4}[-/]\d{2}[-/]\d{2}(?:\s+\d{2}:\d{2}:\d{2})?\b'),
            "btc": re.compile(r'\b(?:1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,39}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "iban": re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b'),
            "base64": re.compile(r'\b(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\b'),
            "hex": re.compile(r'\b(?:0x)?[0-9a-fA-F]{16,}\b')
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if mode_key == "specific_word":
                        if not specific_word: continue
                        matches = re.finditer(r'(?i)\b' + re.escape(specific_word) + r'\b', line)
                        for match in matches:
                            results.add(match.group(0))
                            
                    elif mode_key == "readable":
                        words = patterns["readable"].findall(line)
                        for w in words:
                            if w.lower() != "null":
                                results.add(w)
                    else:
                        for match in patterns[mode_key].findall(line):
                            if mode_key == "credit_card" and len(re.sub(r'\D', '', match)) < 13: continue
                            if mode_key == "phone" and len(re.sub(r'\D', '', match)) < 10: continue
                            results.add(match.strip())
            return results
        except Exception as e:
            return e

    def start_processing(self):
        L = LANG[self.current_lang]
        mode_key = self.extraction_mode_var.get()
        specific_word = self.word_entry.get().strip()
        
        if mode_key == "specific_word" and not specific_word:
            messagebox.showerror(L["msg_title_err"], L["msg_req_keyword"])
            return

        self.start_btn.configure(state="disabled", text=L["btn_processing"])
        self.select_btn.configure(state="disabled")
        self.output_btn.configure(state="disabled")
        self.status_label.configure(text=L["status_op"].format(L["modes"][mode_key].upper()), text_color="#E53935")
        
        self.log("\n" + "-"*40)
        self.log(f"--- M[{mode_key.upper()}] | T[{len(self.files_to_process)}]")
        self.log("-" * 40)
        
        threading.Thread(target=self._run_multithreaded_extraction, args=(mode_key, specific_word), daemon=True).start()

    def _run_multithreaded_extraction(self, mode_key, specific_word):
        master_results = set()
        total_files = len(self.files_to_process)
        processed_count = 0
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_fp = {executor.submit(self.process_file_task, fp, mode_key, specific_word): fp for fp in self.files_to_process}
            
            for future in concurrent.futures.as_completed(future_to_fp):
                fp = future_to_fp[future]
                filename = os.path.basename(fp)
                try:
                    result = future.result()
                    if isinstance(result, Exception):
                        self.after(0, self.log, f"[!] ERROR {filename}: {str(result)}")
                    else:
                        master_results.update(result)
                        processed_count += 1
                        progress = processed_count / total_files
                        self.after(0, self.progress_bar.set, progress)
                        self.after(0, self.log, f"[+] {filename} -> {len(result)} items clean.")
                except Exception as e:
                    self.after(0, self.log, f"[x] CRASH {filename}: {str(e)}")

        self.after(0, self.log, f"\n[*] EXPORTING CLEAN DATA...")
        
        try:
            with open(self.output_path, 'w', encoding='utf-8') as out_f:
                for item in sorted(master_results, key=lambda x: str(x).lower()):
                    out_f.write(str(item) + '\n')
            self.after(0, self.log, f"[+] SAVED: {len(master_results)} ITEMS WRITTEN.")
        except Exception as e:
            self.after(0, self.log, f"[!] WRITE ERROR: {str(e)}")

        elapsed = round(time.time() - start_time, 2)
        self.after(0, self.log, f"[*] TIME: {elapsed}s")
        self.after(0, self.log, "-"*40 + "\n")
        
        self.after(0, self._finish_ui_reset)

    def _finish_ui_reset(self):
        L = LANG[self.current_lang]
        self.start_btn.configure(state="normal", text=L["btn_start"])
        self.select_btn.configure(state="normal")
        self.output_btn.configure(state="normal")
        self.status_label.configure(text=L["status_idle"], text_color="#1976D2")
        messagebox.showinfo(L["msg_title_ok"], L["msg_complete"])

if __name__ == "__main__":
    app = PathExtractorApp()
    app.mainloop()
