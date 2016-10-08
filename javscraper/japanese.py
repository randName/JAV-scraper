import re

MORAS = tuple(c.strip() + v for c in ' kstnhmr' for v in 'aiueo')
MORAS += ('ya','yu','yo','wa','wo','nn')

def normalize(t):
    """Standardize characters."""
    return re.sub('〜','～',t)
