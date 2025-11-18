"""
Bitcoin wallet generation module.

This module provides functionality to generate Bitcoin wallets using
BIP-39 mnemonic phrases and derive Bitcoin addresses.
"""
import mnemonic
import bitcoin
from typing import Dict, Optional


def generate_wallet() -> Optional[Dict[str, str]]:
    """
    Generate a new Bitcoin wallet with mnemonic phrase, private key, and address.
    
    Returns:
        Dictionary containing:
            - mnemonic: 24-word mnemonic phrase
            - private_key: Hexadecimal private key
            - address: Bitcoin address
        Returns None if generation fails.
    """
    try:
        mnemo = mnemonic.Mnemonic("english")
        secret_phrase = mnemo.generate(strength=256)
        
        if not mnemo.check(secret_phrase):
            return None

        seed = mnemo.to_seed(secret_phrase)

        priv_key = bitcoin.sha256(seed)

        pub_key = bitcoin.privtopub(priv_key)
        address = bitcoin.pubtoaddr(pub_key)

        return {
            "mnemonic": secret_phrase,
            "private_key": priv_key,
            "address": address
        }
    except Exception as e:
        # Log error would be better, but keeping it simple for now
        return None
