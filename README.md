# Pure-Data Purifier 🛡️

**Pure-Data Purifier** is an advanced, high-performance forensic and data extraction tool built with Python. Designed with a sleek, modern UI, it effortlessly sweeps through enormous, heavily corrupted, or garbage-filled files to extract only the clean, structured data you need. 

Developed by **Anwar Yousef**, this tool acts as a powerful parser capable of handling highly unstructured data sets and returning clean intelligence spanning from system paths all the way to cryptography hashes and financial identifiers.

---

## ✨ Key Features

- **Blazing Fast Multi-Threading Processing**: Analyzes multiple massive files simultaneously without freezing the UI, taking full advantage of modern multi-core CPUs.
- **Garbage Agnostic**: Completely ignores symbols, `null` strings, encoding errors, and unstructured mess. It only targets what you command it to look for.
- **Export Flexibility**: Save your extracted datasets as `.txt`, `.csv`, `.json`, or any format (`*.*`).
- **De-Duplication Engine**: Automatically removes duplicate hits and sorts the final list alphabetically before exporting.
- **Multilingual Support**: Switch seamlessly between **English** and **Deutsch** from within the app.
- **Live Terminal Log**: A modern built-in terminal that tracks processing stages, file extraction counts, and error reports in real-time.
- **Beautiful Light UI**: A comfortable Ocean Blue / Brilliant White graphical interface built using the modern `CustomTkinter` library.

---

## 🔍 Data Extraction Modes (Over 20+ Engines integrated via Tabview)

The tool is divided into 4 intelligent categories:

### 1. General & System
- **Clean File Paths (`//dir/...`)**: Specifically crafted Engine to safely extract the longest overlapping directories and Linux/Windows path patterns.
- **Extract Clean Text Only**: Filters out everything unreadable and extracts ONLY intelligent, human-readable words.
- **Specific Keyword Match**: Search for a specific word deeply buried in an immense log (e.g., `password`).
- **Windows Registry Keys**: Extract `HKLM`, `HKCU`, and other registry paths.
- **Dates & Timestamps**: Pull standard Date and Time formats `YYYY-MM-DD HH:MM:SS`.

### 2. Network & Web
- **IPv4 & IPv6 Addresses**
- **Domains** (e.g., `google.com`)
- **URLs** (`http/https`)
- **Email Addresses**
- **MAC Addresses**

### 3. Identity & Finance
- **Phone Numbers (Global format)**
- **Credit Card Numbers**
- **Bitcoin Addresses**
- **Social Security Numbers (SSN)**
- **IBAN Account Numbers**

### 4. Crypto & Forensics
- **MD5 Hashes** (32 characters)
- **SHA Hashes** (SHA-1 / SHA-256)
- **Base64 Encoded Payloads** (Extract embedded commands/scripts)
- **Hexadecimal Strings** (`0x00...`)

---

## 🚀 Installation & Setup

1. **Prerequisites**: Ensure you have Python 3.8+ installed on your machine.
2. **Install Dependencies**:
   Open your terminal and install the required modules:
   ```bash
   pip install customtkinter pillow
