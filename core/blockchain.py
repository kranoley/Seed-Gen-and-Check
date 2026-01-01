import requests


def check_balance(address, proxy_line="", proxy_format="{proxy}", proxy_type="http", timeout=10):
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
        except Exception as e:
            return None

    try:
        response = requests.get(url, proxies=proxies, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            balance = data.get("final_balance", 0)
            txs = data.get("n_tx", 0)
            return {"balance": balance, "txs": txs}
        
        elif response.status_code == 404:
            return {"balance": 0, "txs": 0}
        
        else:
            return None

    except requests.exceptions.RequestException:
        return None
