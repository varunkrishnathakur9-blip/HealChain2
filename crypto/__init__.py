"""
Crypto module for HealChain.

This module contains cryptographic primitives:
- ndd_fe: Non-Interactive Decentralized Decryption Functional Encryption (functions)
- DGC: Decentralized Gradient Compression
"""

from . import ndd_fe
from .ndd_fe import key_gen, key_derive, encrypt_integer_vector, decrypt_aggregate, curve
from .dgc import DGC, calculate_contribution_score_from_sparse


__all__ = [
    'ndd_fe',
    'key_gen',
    'key_derive', 
    'encrypt_integer_vector',
    'decrypt_aggregate',
    'curve',
    'DGC',
    'calculate_contribution_score_from_sparse'
]