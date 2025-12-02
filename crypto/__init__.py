"""
Crypto module for HealChain.

This module contains cryptographic primitives:
- NDD_FE: Non-Interactive Decentralized Decryption Functional Encryption
- DGC: Decentralized Gradient Compression
"""

# FIX: Import from 'nddfe' to match the filename 'nddfe.py' created in the previous step.
# If you renamed the file to 'ndd_fe.py', use 'from .ndd_fe import NDD_FE' instead.
from .ndd_fe import NDD_FE
from .dgc import DGC, calculate_contribution_score

__all__ = ['NDD_FE', 'DGC', 'calculate_contribution_score']