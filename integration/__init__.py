"""
Integration module for HealChain.

This module provides integration between the blockchain layer and federated learning layer:
- Web3Client: Handles blockchain interactions
- simulation_runner: Orchestrates the full HealChain workflow
"""

from .web3_client import Web3Client

__all__ = ['Web3Client']

