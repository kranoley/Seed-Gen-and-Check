  
_A Bitcoin wallet generator and balance checker_

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![UI](https://img.shields.io/badge/UI-CustomTkinter-orange.svg)
![Bitcoin](https://img.shields.io/badge/Bitcoin-Tools-yellow.svg)

---

## 🌍 Overview

**Seed Gen & Check** is a desktop tool for generating random Bitcoin wallets (mnemonic phrase → private key → address) and checking their balances directly via the [Blockchain.info API](https://www.blockchain.com/api/blockchain_api).  
It features a clean graphical interface built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) and supports multi-threaded scanning with optional proxy support.



---

## ✨ Features

- 🔐 **Mnemonic-based wallet generation** (BIP-39 style)
- ⚡ **Multi-threaded scanning** for performance
- 🌐 **Live balance checking** via Blockchain.info API
- 🧩 **Proxy support** (HTTP/SOCKS)
- 💾 **Automatic results saving** (found wallets → `results.txt`)
- 🎨 **Modern dark-themed GUI**

---

## 📦 Installation

1. [Download source code](https://github.com/kranoley/Seed-Gen-and-Check/archive/refs/heads/main.zip)
   
2. Install dependencies

`pip install -r requirements.txt`

or install manually:

`pip install customtkinter mnemonic bitcoin requests`


3. Run the application

`python main.py`




---

🖥️ Usage

1. Launch the app — the interface opens in a dark theme.


2. Set your preferences:

Number of threads

Delay between requests

Proxy type and format (optional)



3. Click Start to begin scanning.


4. Watch logs in the window.


5. When a wallet with non-zero balance is found, it will be saved to:

`results.txt`


---



⚠️ Legal & Ethical Notice

This software must not be used for illegal activities.
The author assume no responsibility for misuse or violations of applicable laws.
Always act ethically when experimenting with blockchain technology.


---
