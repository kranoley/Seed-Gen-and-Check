import customtkinter as ctk
from gui.app import BitcoinScannerApp

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    app = BitcoinScannerApp(root)
    root.mainloop()
