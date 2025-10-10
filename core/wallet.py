import mnemonic
import bitcoin


def generate_wallet():
    mnemo = mnemonic.Mnemonic("english")
    secret_phrase = mnemo.generate(strength=256)

    seed = mnemo.to_seed(secret_phrase)

    priv_key = bitcoin.sha256(seed)

    pub_key = bitcoin.privtopub(priv_key)
    address = bitcoin.pubtoaddr(pub_key)

    return {
        "mnemonic": secret_phrase,
        "private_key": priv_key,
        "address": address
    }
