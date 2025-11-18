"""
Bitcoin wallet scanner module.

This module provides a multi-threaded scanner that generates wallets
and checks their balances on the blockchain.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Callable, Optional
import os
from .wallet import generate_wallet
from .blockchain import check_balance


class BitcoinScanner:
    """
    Multi-threaded Bitcoin wallet scanner.
    
    Generates random wallets and checks their balances using
    configurable threading and proxy support.
    """
    
    def __init__(
        self,
        settings: Dict,
        proxy_line: str = "",
        on_log: Optional[Callable[[str, str], None]] = None,
        on_found: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None
    ):
        """
        Initialize the scanner.
        
        Args:
            settings: Dictionary with scanner settings (threads, delay, limit_per_thread, etc.)
            proxy_line: Proxy string to use for requests
            on_log: Callback function(msg, color) for logging
            on_found: Callback function() when a wallet with balance is found
            on_stop: Callback function() when scanning stops
        """
        self.settings = settings
        self.proxy_line = proxy_line
        self.on_log = on_log or (lambda msg, color="white": None)
        self.on_found = on_found or (lambda: None)
        self.on_stop = on_stop or (lambda: None)

        self.is_running = False
        self.executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
        self._total_checked = 0

    def start(self) -> None:
        """Start the scanning process."""
        with self._lock:
            if self.is_running:
                self.on_log("[!] Scanner is already running", "yellow")
                return
            self.is_running = True

        controller_thread = threading.Thread(target=self._run_controller, daemon=True)
        controller_thread.start()
        self.on_log("[+] Scanner started", "green")

    def stop(self) -> None:
        """Stop the scanning process."""
        with self._lock:
            if not self.is_running:
                return
            self.is_running = False

        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        
        self.on_log(f"[!] Scanner stopped. Total checked: {self._total_checked}", "yellow")
        self.on_stop()

    def _run_controller(self) -> None:
        """Control thread that manages worker threads."""
        try:
            max_workers = max(1, min(self.settings.get("threads", 4), 50))  # Limit to reasonable range
            self.executor = ThreadPoolExecutor(max_workers=max_workers)

            futures = []
            for i in range(max_workers):
                future = self.executor.submit(
                    self._worker,
                    worker_id=i,
                    limit=self.settings.get("limit_per_thread", 1000),
                    delay=self.settings.get("delay", 1.0)
                )
                futures.append(future)

            # Wait for all workers to complete or be cancelled
            for future in as_completed(futures):
                try:
                    future.result(timeout=1)
                except Exception as e:
                    if self.is_running:
                        self.on_log(f"[!] Worker error: {e}", "yellow")

        except Exception as e:
            self.on_log(f"[!] Controller error: {e}", "red")
        finally:
            if self.is_running:
                with self._lock:
                    self.is_running = False
                self.on_stop()

    def _worker(self, worker_id: int, limit: float, delay: float) -> None:
        """
        Worker thread that generates wallets and checks balances.
        
        Args:
            worker_id: Unique identifier for this worker
            limit: Maximum number of wallets to check (float('inf') for unlimited)
            delay: Delay between checks in seconds
        """
        count = 0
        consecutive_errors = 0
        max_consecutive_errors = 10

        while (limit == float('inf') or count < limit) and self.is_running:
            try:
                wallet = generate_wallet()
                if wallet is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.on_log(f"[!] Worker {worker_id}: Too many generation errors", "red")
                        break
                    time.sleep(0.5)
                    continue

                consecutive_errors = 0
                secret_phrase = wallet["mnemonic"]
                address = wallet["address"]

                balance_info = check_balance(
                    address=address,
                    proxy_line=self.proxy_line,
                    proxy_format=self.settings.get("proxy_format", "{proxy}"),
                    proxy_type=self.settings.get("proxy_type", "http"),
                    timeout=self.settings.get("timeout", 10)
                )

                with self._lock:
                    self._total_checked += 1

                if balance_info is None:
                    self.on_log(f"[!] Failed to check {address[:10]}...", "yellow")
                else:
                    balance = balance_info["balance"]
                    txs = balance_info["txs"]
                    if balance > 0 or txs > 0:
                        result_line = f"{address} : {secret_phrase}"
                        self._save_result(result_line)
                        self.on_found()
                        self.on_log(f"[+] FOUND! {result_line}", "green")
                    else:
                        if count % 10 == 0:  # Log every 10th to reduce spam
                            limit_str = "∞" if limit == float('inf') else str(limit)
                            self.on_log(
                                f"[{worker_id}] Checked {count}/{limit_str} | Total: {self._total_checked}",
                                "gray"
                            )

                if delay > 0:
                    time.sleep(delay)
                count += 1

            except KeyboardInterrupt:
                break
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.on_log(f"[!] Worker {worker_id}: Too many errors: {e}", "red")
                    break
                self.on_log(f"[!] Worker {worker_id} exception: {e}", "yellow")
                time.sleep(min(delay, 1.0))

        if self.is_running:
            self.on_log(f"[*] Worker {worker_id} finished ({count} checked)", "gray")

    def _save_result(self, line: str) -> None:
        """
        Save a found wallet result to file.
        
        Args:
            line: Line to write to results file
        """
        results_file = self.settings.get("results_file", "results.txt")
        try:
            with open(results_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()  # Ensure immediate write
        except IOError as e:
            self.on_log(f"[!] Failed to write to {results_file}: {e}", "red")
        except Exception as e:
            self.on_log(f"[!] Unexpected error writing result: {e}", "red")
