#!/usr/bin/env python3
"""
Utility script to view all stored invoice links
"""
import json
from datetime import datetime

def view_invoice_links():
    """Display all stored invoice links in a readable format"""
    try:
        with open("invoice_links.json", "r", encoding="utf-8") as f:
            invoice_links = json.load(f)
        
        if not invoice_links:
            print("No invoice links found.")
            return
        
        print(f"Found {len(invoice_links)} invoice links:\n")
        print("-" * 80)
        
        for i, invoice in enumerate(invoice_links, 1):
            timestamp = datetime.fromisoformat(invoice["timestamp"])
            print(f"{i}. Order ID: {invoice['order_id']}")
            print(f"   Invoice Number: {invoice['invoice_number']}")
            print(f"   Total Amount: {invoice['total_amount']} RON")
            print(f"   Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Link: {invoice['invoice_link']}")
            print("-" * 80)
            
    except FileNotFoundError:
        print("No invoice links file found. Run main.py first to generate invoices.")
    except json.JSONDecodeError:
        print("Error reading invoice links file. File may be corrupted.")

if __name__ == "__main__":
    view_invoice_links()