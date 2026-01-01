import os
import threading
import customtkinter as ctk

from core.scanner import BitcoinScanner  


class BitcoinScannerApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bitcoin Wallet Scanner")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.is_scanning = False
        self.found_count = 0
        self.log_queue = []
        self.log_lock = threading.Lock()

        self.tabview = ctk.CTkTabview(root, width=750, height=520)
        self.tabview.pack(padx=20, pady=20)

        self.scan_tab = self.tabview.add("Scan")
        self.settings_tab = self.tabview.add("Settings")

        self.setup_scan_tab()
        self.setup_settings_tab()

        self.process_log_queue()

    def setup_scan_tab(self):
        self.action_button = ctk.CTkButton(
            self.scan_tab, text="Start", command=self.toggle_scanning, width=120
        )
        self.action_button.place(x=50, y=20)

        self.status_label = ctk.CTkLabel(self.scan_tab, text="Ready", font=("Arial", 12))
        self.status_label.place(x=50, y=60)

        self.log_text = ctk.CTkTextbox(
            self.scan_tab, width=700, height=400, wrap="word", font=("Consolas", 12)
        )
        self.log_text.place(x=25, y=100)

    def setup_settings_tab(self):
        y_offset = 30

        self.proxy_checkbox = ctk.CTkCheckBox(
            self.settings_tab, text="Use Proxy", command=self.toggle_proxy_fields
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
            self.settings_tab, text="Proxy Format (use {proxy}):"
        )
        self.proxy_format_label.place(x=30, y=y_offset)
        self.proxy_format_entry = ctk.CTkEntry(self.settings_tab, width=300)
        self.proxy_format_entry.insert(0, "{proxy}")
        self.proxy_format_entry.place(x=30, y=y_offset + 25)
        y_offset += 60

        self.threads_label = ctk.CTkLabel(self.settings_tab, text="Number of Threads:")
        self.threads_label.place(x=30, y=y_offset)
        self.threads_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.threads_entry.insert(0, "4")
        self.threads_entry.place(x=180, y=y_offset)
        y_offset += 40

        self.delay_label = ctk.CTkLabel(
            self.settings_tab, text="Delay between requests (seconds):"
        )
        self.delay_label.place(x=30, y=y_offset)
        self.delay_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.delay_entry.insert(0, "1")
        self.delay_entry.place(x=240, y=y_offset)
        y_offset += 40

        self.limit_label = ctk.CTkLabel(self.settings_tab, text="Addresses per thread:")
        self.limit_label.place(x=30, y=y_offset)
        self.limit_entry = ctk.CTkEntry(self.settings_tab, width=80)
        self.limit_entry.insert(0, "1000")
        self.limit_entry.place(x=180, y=y_offset)

        self.toggle_proxy_fields()

    def toggle_proxy_fields(self):
        state = "normal" if self.proxy_checkbox.get() else "disabled"
        self.proxy_type_combo.configure(state=state)
        self.proxy_format_entry.configure(state=state)

    def get_settings(self):
        try:
            return {
                "use_proxy": bool(self.proxy_checkbox.get()),
                "proxy_type": self.proxy_type_combo.get(),
                "proxy_format": self.proxy_format_entry.get(),
                "threads": int(self.threads_entry.get()),
                "delay": float(self.delay_entry.get()),
                "limit_per_thread": int(self.limit_entry.get()),
            }
        except ValueError:
            self.log_message("Invalid settings: please enter valid numbers.", "yellow")
            return None

    def log_message(self, message, color="white"):
        with self.log_lock:
            self.log_queue.append((message, color))

    def process_log_queue(self):
        with self.log_lock:
            while self.log_queue:
                msg, color = self.log_queue.pop(0)
                self.log_text.insert("end", msg + "\n", color)
                self.log_text.tag_config(color, foreground=color)
                self.log_text.see("end")
        self.root.after(100, self.process_log_queue)

    def toggle_scanning(self):
        if self.is_scanning:
            self.stop_scanning()
        else:
            self.start_scanning()

    def start_scanning(self):
        settings = self.get_settings()
        if not settings:
            return


        proxy_line = ""
        if settings["use_proxy"] and os.path.exists("proxy.txt"):
            with open("proxy.txt") as f:
                proxy_line = f.readline().strip()


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
        self.status_label.configure(text="Scanning...")

        self.scanner.start()

    def stop_scanning(self):
        if hasattr(self, 'scanner'):
            self.scanner.stop()

    def increment_found(self):
        self.found_count += 1

    def scanning_finished(self):
        self.is_scanning = False
        self.action_button.configure(text="Start")
        self.status_label.configure(text=f"Stopped. Found: {self.found_count}")
        self.log_message("Scanning stopped.", "yellow")
