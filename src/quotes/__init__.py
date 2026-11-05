"""Quotes module for ContextCon 04 Hackathon.
Handles simulated supplier quote collection, validation, and provenance preservation.
"""
from .models import Quote
from .collector import QuoteCollector

__all__ = ["Quote", "QuoteCollector"]

