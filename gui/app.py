"""
GUI application for Bitcoin wallet scanner.

This module provides a CustomTkinter-based graphical interface
for the Bitcoin wallet scanner.
"""
import os
import threading
import customtkinter as ctk
from typing import Optional
from core.scanner import BitcoinScanner  


class BitcoinScannerApp:
    """Main application window for Bitcoin wallet scanner."""
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize the application.
        
        Args:
            root: CustomTkinter root window
        """
        self.root = root
        self.root.title("Bitcoin Wallet Scanner")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)

        self.is_scanning = False
        self.found_count = 0
        self.log_queue = []
        self.log_lock = threading.Lock()
        self.scanner: Optional[BitcoinScanner] = None

        self.tabview = ctk.CTkTabview(root, width=750, height=520)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.scan_tab = self.tabview.add("Scan")
        self.settings_tab = self.tabview.add("Settings")

        self.setup_scan_tab()
        self.setup_settings_tab()

        self.process_log_queue()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_scan_tab(self) -> None:
        """Set up the scanning tab UI."""
        self.action_button = ctk.CTkButton(
            self.scan_tab,
            text="Start",
            command=self.toggle_scanning,
            width=120,
            height=35,
            font=("Arial", 14, "bold")
        )
        self.action_button.place(x=50, y=20)

        self.status_label = ctk.CTkLabel(
            self.scan_tab,
            text="Ready",
            font=("Arial", 12)
        )
        self.status_label.place(x=200, y=28)

        self.found_label = ctk.CTkLabel(
            self.scan_tab,
            text="Found: 0",
            font=("Arial", 12),
            text_color="green"
        )
        self.found_label.place(x=50, y=60)

        self.log_text = ctk.CTkTextbox(
            self.scan_tab,
            width=700,
            height=400,
            wrap="word",
            font=("Consolas", 11)
        )
        self.log_text.place(x=25, y=100)
        
        # Configure text colors
        self.log_text.tag_config("white", foreground="white")
        self.log_text.tag_config("green", foreground="#00ff00")
        self.log_text.tag_config("yellow", foreground="#ffff00")
        self.log_text.tag_config("red", foreground="#ff0000")
        self.log_text.tag_config("gray", foreground="#808080")

    def setup_settings_tab(self) -> None:
        """Set up the settings tab UI."""
        y_offset = 30

        self.proxy_checkbox = ctk.CTkCheckBox(
            self.settings_tab,
            text="Use Proxy",
            command=self.toggle_proxy_fields
        )
        self.proxy_checkbox.place(x=30, y=y_offset)
        y_offset += 40

        self.proxy_type_label = ctk.CTkLabel(self.settings_tab, text="Proxy Type:")
        self.proxy_type_label.place(x=30, y=y_offset)
        self.proxy_type_combo = ctk.CTkComboBox(
            self.settings_tab,
            values=["http", "https", "socks4", "socks5"],
            width=120,
        )
        self.proxy_type_combo.set("http")
        self.proxy_type_combo.place(x=150, y=y_offset)
        y_offset += 40

        self.proxy_format_label = ctk.CTkLabel(
            self.settings_tab,
            text="Proxy Format (use {proxy}):"
        )
        self.proxy_format_label.place(x=30, y=y_offset)
        self.proxy_format_entry = ctk.CTkEntry(self.settings_tab, width=300)
        self.proxy_format_entry.insert(0, "{proxy}")
        self.proxy_format_entry.place(x=30, y=y_offset + 25)
        y_offset += 60

        self.threads_label = ctk.CTkLabel(
            self.settings_tab,
            text="Number of Threads (1-50):"
        )
        self.threads_label.place(x=30, y=y_offset)
        self.threads_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.threads_entry.insert(0, "4")
        self.threads_entry.place(x=200, y=y_offset)
        y_offset += 40

        self.delay_label = ctk.CTkLabel(
            self.settings_tab,
            text="Delay between requests (seconds):"
        )
        self.delay_label.place(x=30, y=y_offset)
        self.delay_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.delay_entry.insert(0, "1.0")
        self.delay_entry.place(x=240, y=y_offset)
        y_offset += 40

        self.limit_label = ctk.CTkLabel(
            self.settings_tab,
            text="Addresses per thread (0 = unlimited):"
        )
        self.limit_label.place(x=30, y=y_offset)
        self.limit_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.limit_entry.insert(0, "1000")
        self.limit_entry.place(x=280, y=y_offset)
        y_offset += 40

        self.timeout_label = ctk.CTkLabel(
            self.settings_tab,
            text="Request timeout (seconds):"
        )
        self.timeout_label.place(x=30, y=y_offset)
        self.timeout_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.timeout_entry.insert(0, "10")
        self.timeout_entry.place(x=200, y=y_offset)

        self.toggle_proxy_fields()

    def toggle_proxy_fields(self) -> None:
        """Enable/disable proxy fields based on checkbox state."""
        state = "normal" if self.proxy_checkbox.get() else "disabled"
        self.proxy_type_combo.configure(state=state)
        self.proxy_format_entry.configure(state=state)

    def get_settings(self) -> Optional[dict]:
        """
        Get and validate settings from UI.
        
        Returns:
            Dictionary with settings or None if validation fails.
        """
        try:
            threads = int(self.threads_entry.get())
            if threads < 1 or threads > 50:
                raise ValueError("Threads must be between 1 and 50")
            
            delay = float(self.delay_entry.get())
            if delay < 0:
                raise ValueError("Delay must be non-negative")
            
            limit = int(self.limit_entry.get())
            if limit < 0:
                raise ValueError("Limit must be non-negative")
            
            timeout = int(self.timeout_entry.get())
            if timeout < 1 or timeout > 300:
                raise ValueError("Timeout must be between 1 and 300 seconds")
            
            proxy_format = self.proxy_format_entry.get()
            if "{proxy}" not in proxy_format:
                raise ValueError("Proxy format must contain {proxy} placeholder")
            
            return {
                "use_proxy": bool(self.proxy_checkbox.get()),
                "proxy_type": self.proxy_type_combo.get(),
                "proxy_format": proxy_format,
                "threads": threads,
                "delay": delay,
                "limit_per_thread": limit if limit > 0 else float('inf'),
                "timeout": timeout,
                "results_file": "results.txt"
            }
        except ValueError as e:
            self.log_message(f"Invalid settings: {e}", "red")
            return None
        except Exception as e:
            self.log_message(f"Error reading settings: {e}", "red")
            return None

    def log_message(self, message: str, color: str = "white") -> None:
        """
        Queue a log message for display.
        
        Args:
            message: Message to log
            color: Color for the message
        """
        with self.log_lock:
            self.log_queue.append((message, color))

    def process_log_queue(self) -> None:
        """Process queued log messages and display them."""
        with self.log_lock:
            while self.log_queue:
                msg, color = self.log_queue.pop(0)
                self.log_text.insert("end", msg + "\n", color)
                self.log_text.see("end")
        
        # Limit log size to prevent memory issues
        if int(self.log_text.index("end-1c").split(".")[0]) > 1000:
            self.log_text.delete("1.0", "500.0")
        
        self.root.after(100, self.process_log_queue)

    def toggle_scanning(self) -> None:
        """Toggle scanning on/off."""
        if self.is_scanning:
            self.stop_scanning()
        else:
            self.start_scanning()

    def start_scanning(self) -> None:
        """Start the scanning process."""
        settings = self.get_settings()
        if not settings:
            return

        proxy_line = ""
        if settings["use_proxy"]:
            proxy_file = "proxy.txt"
            if os.path.exists(proxy_file):
                try:
                    with open(proxy_file, "r", encoding="utf-8") as f:
                        proxy_line = f.readline().strip()
                    if not proxy_line:
                        self.log_message("[!] Proxy file is empty", "yellow")
                except IOError as e:
                    self.log_message(f"[!] Failed to read proxy file: {e}", "red")
            else:
                self.log_message("[!] proxy.txt not found", "yellow")

        self.scanner = BitcoinScanner(
            settings=settings,
            proxy_line=proxy_line,
            on_log=self.log_message,
            on_found=self.increment_found,
            on_stop=self.scanning_finished
        )

        self.is_scanning = True
        self.found_count = 0
        self.action_button.configure(text="Stop")
        self.status_label.configure(text="Scanning...", text_color="green")
        self.found_label.configure(text="Found: 0")

        self.log_message("[+] Starting scanner...", "green")
        self.scanner.start()

    def stop_scanning(self) -> None:
        """Stop the scanning process."""
        if self.scanner:
            self.scanner.stop()
        self.log_message("[!] Stopping scanner...", "yellow")

    def increment_found(self) -> None:
        """Increment the found counter and update UI."""
        self.found_count += 1
        self.found_label.configure(text=f"Found: {self.found_count}")

    def scanning_finished(self) -> None:
        """Handle scanning completion."""
        self.is_scanning = False
        self.action_button.configure(text="Start")
        self.status_label.configure(
            text=f"Stopped. Found: {self.found_count}",
            text_color="white"
        )
        self.log_message(f"[*] Scanning finished. Found {self.found_count} wallet(s).", "yellow")

    def on_closing(self) -> None:
        """Handle window close event."""
        if self.is_scanning:
            self.stop_scanning()
            # Wait a bit for cleanup
            self.root.after(500, self.root.destroy)
        else:
            self.root.destroy()
