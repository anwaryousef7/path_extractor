import struct
import string
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

def extract_readable_strings(data, min_length=4):
    """Extract readable text from binary data."""
    printable = set(string.printable.encode())
    result = []
    current_string = bytearray()
    
    for byte in data:
        if byte in printable:
            current_string.append(byte)
        else:
            if len(current_string) >= min_length:
                result.append(current_string.decode('ascii', errors='ignore').strip())
            current_string = bytearray()
            
    if len(current_string) >= min_length:
        result.append(current_string.decode('ascii', errors='ignore').strip())
    
    return result

def parse_sophos_riff(file_path):
    """Parse a single RIFF file and return the formatted string."""
    output = []
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found!"

    try:
        with open(file_path, 'rb') as f:
            riff_header = f.read(4)
            if riff_header != b'RIFF':
                return f"[!] Skipping '{os.path.basename(file_path)}': Not a valid RIFF file."

            file_size = struct.unpack('<I', f.read(4))[0]
            form_type = f.read(4).decode('ascii', errors='ignore')
            
            output.append("=" * 80)
            output.append(f" FILE: {os.path.basename(file_path)}")
            output.append("=" * 80)
            output.append(f" Path: {file_path}")
            output.append(f" Reported Size: {file_size} bytes")
            output.append(f" Internal Type: {form_type}")
            output.append("-" * 80)
            
            chunk_count = 1
            strings_found = False
            
            while True:
                chunk_id_bytes = f.read(4)
                if not chunk_id_bytes or len(chunk_id_bytes) < 4:
                    break
                
                chunk_id = chunk_id_bytes.decode('ascii', errors='ignore')
                
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    break
                
                chunk_size = struct.unpack('<I', size_bytes)[0]
                chunk_data = f.read(chunk_size)
                
                strings = extract_readable_strings(chunk_data)
                
                if strings:
                    strings_found = True
                    output.append(f"  [Chunk {chunk_count}: '{chunk_id}' | Size: {chunk_size} bytes]")
                    for s in strings:
                        if s.strip(): 
                            output.append(f"    -> {s}")
                    output.append("") # Empty line for readability
                
                # RIFF standard padding for odd-sized chunks
                if chunk_size % 2 != 0:
                    f.read(1)
                    
                chunk_count += 1
                
            if not strings_found:
                output.append("  [!] No readable strings found in this file (Binary data only).")
                
        return "\n".join(output)
    
    except Exception as e:
        return f"Error processing '{os.path.basename(file_path)}':\n{str(e)}"

def process_files(file_paths):
    """Process a list of files and update the text area."""
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    
    total_files = len(file_paths)
    all_results = []
    
    for index, file_path in enumerate(file_paths, 1):
        text_area.insert(tk.END, f"Analyzing file {index} of {total_files}: {os.path.basename(file_path)}...\n")
        text_area.update()
        
        result = parse_sophos_riff(file_path)
        all_results.append(result)
        all_results.append("\n\n")
        
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, "".join(all_results))
    text_area.config(state=tk.DISABLED)

def browse_files():
    """Select multiple files."""
    file_paths = filedialog.askopenfilenames(title="Select Sophos Files (Select multiple)")
    if file_paths:
        process_files(file_paths)

def browse_folder():
    """Select an entire folder."""
    folder_path = filedialog.askdirectory(title="Select Folder containing Sophos Files")
    if folder_path:
        # Get all files in the selected directory
        file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        if file_paths:
            process_files(file_paths)
        else:
            messagebox.showinfo("Info", "No files found in the selected folder.")

def export_results():
    """Export the text area content to a .txt file."""
    content = text_area.get(1.0, tk.END).strip()
    
    # Check if there is actual data to export
    if not content or "Welcome to the Sophos Analyzer" in content:
        messagebox.showwarning("Warning", "There is no analysis data to export yet!\nPlease analyze files first.")
        return
        
    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt", 
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Export Results As..."
    )
    
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Success", f"Results successfully exported to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

# ==========================================
# GUI Setup
# ==========================================
root = tk.Tk()
root.title("Sophos RIFF Analyzer - Pro Edition")
root.geometry("950x700")
root.configure(bg="#1e1e1e")

# Header
header_frame = tk.Frame(root, bg="#1e1e1e", pady=15)
header_frame.pack(fill=tk.X)

tk.Label(header_frame, text="Sophos RIFF Analyzer PRO", font=("Segoe UI", 22, "bold"), bg="#1e1e1e", fg="#ffffff").pack()
tk.Label(header_frame, text="Batch Processing & Metadata Extraction Tool", font=("Segoe UI", 11), bg="#1e1e1e", fg="#a0a0a0").pack()

# Buttons Frame
buttons_frame = tk.Frame(root, bg="#1e1e1e", pady=10)
buttons_frame.pack(fill=tk.X)

# Center the buttons
buttons_center = tk.Frame(buttons_frame, bg="#1e1e1e")
buttons_center.pack(anchor="center")

# Define button styles
btn_style = {"font": ("Segoe UI", 11, "bold"), "fg": "white", "relief": tk.FLAT, "padx": 20, "pady": 8, "cursor": "hand2"}

# Browse Files Button
btn_files = tk.Button(buttons_center, text="📂 Select Files...", bg="#007acc", activebackground="#005999", activeforeground="white", command=browse_files, **btn_style)
btn_files.pack(side=tk.LEFT, padx=10)

# Browse Folder Button
btn_folder = tk.Button(buttons_center, text="📁 Select Folder...", bg="#d97706", activebackground="#b45309", activeforeground="white", command=browse_folder, **btn_style)
btn_folder.pack(side=tk.LEFT, padx=10)

# Export Button
btn_export = tk.Button(buttons_center, text="💾 Export Results", bg="#10b981", activebackground="#059669", activeforeground="white", command=export_results, **btn_style)
btn_export.pack(side=tk.LEFT, padx=10)

# Output Text Area
text_frame = tk.Frame(root, bg="#1e1e1e", padx=20, pady=10)
text_frame.pack(fill=tk.BOTH, expand=True)

text_area = scrolledtext.ScrolledText(text_frame, font=("Consolas", 11), bg="#2d2d2d", fg="#d4d4d4", insertbackground="white", relief=tk.FLAT, padx=15, pady=15)
text_area.pack(fill=tk.BOTH, expand=True)

# Initial message
welcome_text = """Welcome to the Sophos Analyzer Pro!

Instructions:
1. Click [📂 Select Files...] to choose one or more specific files.
2. Click [📁 Select Folder...] to analyze ALL files inside a specific directory.
3. Once the analysis is complete, click [💾 Export Results] to save the report as a .txt file.

Note: Files that are not valid RIFF formats will be safely skipped.
Ready for analysis...
"""
text_area.insert(tk.END, welcome_text)
text_area.config(state=tk.DISABLED)

root.mainloop()
