import threading
import time
from concurrent.futures import ThreadPoolExecutor
import os

from .wallet import generate_wallet
from .blockchain import check_balance


class BitcoinScanner:
    def __init__(self, settings, proxy_line="", on_log=None, on_found=None, on_stop=None):
        self.settings = settings
        self.proxy_line = proxy_line
        self.on_log = on_log or (lambda msg, color="white": None)
        self.on_found = on_found or (lambda: None)
        self.on_stop = on_stop or (lambda: None)

        self.is_running = False
        self.executor = None
        self.threads = []

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        controller_thread = threading.Thread(target=self._run_controller, daemon=True)
        controller_thread.start()

    def stop(self):
        self.is_running = False
        if self.executor:
            self.executor.shutdown(wait=False)
        self.on_stop()

    def _run_controller(self):
        max_workers = self.settings["threads"]
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        futures = []
        for _ in range(max_workers):
            future = self.executor.submit(
                self._worker,
                limit=self.settings["limit_per_thread"],
                delay=self.settings["delay"]
            )
            futures.append(future)

        for future in futures:
            try:
                future.result()
            except Exception as e:
                self.on_log(f"[!] Worker error: {e}", "yellow")

        if self.is_running:
            self.is_running = False
            self.on_stop()

    def _worker(self, limit, delay):
        count = 0
        while count < limit and self.is_running:
            try:
                wallet = generate_wallet()
                secret_phrase = wallet["mnemonic"]
                address = wallet["address"]

                balance_info = check_balance(
                    address=address,
                    proxy_line=self.proxy_line,
                    proxy_format=self.settings.get("proxy_format", "{proxy}"),
                    proxy_type=self.settings.get("proxy_type", "http"),
                    timeout=10
                )

                if balance_info is None:
                    self.on_log(f"[!] Failed to check {address}", "yellow")
                else:
                    balance = balance_info["balance"]
                    txs = balance_info["txs"]
                    if balance > 0 or txs > 0:
                        result_line = f"{address} : {secret_phrase}"
                        self._save_result(result_line)
                        self.on_found()
                        self.on_log(f"[+] FOUND! {result_line}", "green")
                    else:
                        self.on_log(f"[-] Empty: {address} (balance: {balance}, txs: {txs})", "gray")

                time.sleep(delay)
                count += 1

            except Exception as e:
                self.on_log(f"[!] Worker exception: {e}", "yellow")
                time.sleep(1)

    def _save_result(self, line):
        try:
            with open("results.txt", "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            self.on_log(f"[!] Failed to write to results.txt: {e}", "red")
