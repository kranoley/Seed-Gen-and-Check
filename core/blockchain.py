"""
Blockchain API interaction module.

This module provides functionality to check Bitcoin address balances
via the Blockchain.info API with optional proxy support.
"""
import requests
from typing import Dict, Optional
import time


def check_balance(
    address: str,
    proxy_line: str = "",
    proxy_format: str = "{proxy}",
    proxy_type: str = "http",
    timeout: int = 10,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Optional[Dict[str, int]]:
    """
    Check the balance and transaction count for a Bitcoin address.
    
    Args:
        address: Bitcoin address to check
        proxy_line: Proxy string (e.g., "ip:port" or "user:pass@ip:port")
        proxy_format: Format string for proxy (use {proxy} placeholder)
        proxy_type: Type of proxy (http, https, socks4, socks5)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Dictionary with "balance" (in satoshis) and "txs" (transaction count),
        or None if the check failed.
    """
    if not address or not isinstance(address, str):
        return None
    
    url = f"https://blockchain.info/rawaddr/{address}"

    proxies = {}
    if proxy_line.strip():
        try:
            proxy_url = proxy_format.format(proxy=proxy_line.strip())
            proxy_full = f"{proxy_type}://{proxy_url}"
            proxies = {
                "http": proxy_full,
                "https": proxy_full
            }
        except (KeyError, ValueError, AttributeError):
            return None

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                proxies=proxies if proxies else None,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if response.status_code == 200:
                data = response.json()
                balance = data.get("final_balance", 0)
                txs = data.get("n_tx", 0)
                return {"balance": balance, "txs": txs}
            
            elif response.status_code == 404:
                # Address exists but has no transactions
                return {"balance": 0, "txs": 0}
            
            elif response.status_code == 429:
                # Rate limited - wait longer before retry
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 2))
                    continue
                return None
            
            else:
                # Other HTTP errors - retry if attempts remain
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None
        except (ValueError, KeyError):
            # JSON parsing error
            return None
    
    return None
