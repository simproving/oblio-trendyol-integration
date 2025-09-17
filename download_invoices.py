#!/usr/bin/env python3
"""
Script to download all invoice files from invoice_links.json
Avoids duplicates by checking existing files and tracking downloaded invoices
"""
import json
import requests
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import time

def create_downloads_folder():
    """Create downloads folder with current date"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    downloads_folder = f"downloaded_invoices_{current_date}"
    if not os.path.exists(downloads_folder):
        os.makedirs(downloads_folder)
        print(f"📁 Created folder: {downloads_folder}")
    return downloads_folder

def get_filename_from_invoice_number(invoice_number):
    """Generate filename based on invoice number only"""
    filename = f"Trendyol_Factura_{invoice_number}.pdf"
    return filename

def filter_latest_invoices(invoice_data):
    """Keep only the latest invoice for each invoice number"""
    # Group invoices by invoice number
    invoice_groups = {}
    
    for invoice in invoice_data:
        invoice_number = invoice.get("invoice_number", "unknown")
        timestamp = invoice.get("timestamp", "")
        
        if invoice_number not in invoice_groups:
            invoice_groups[invoice_number] = invoice
        else:
            # Compare timestamps and keep the latest one
            if timestamp > invoice_groups[invoice_number].get("timestamp", ""):
                print(f"🔄 Replacing older invoice {invoice_number} with newer version")
                invoice_groups[invoice_number] = invoice
            else:
                print(f"⏭️  Skipping older version of invoice {invoice_number}")
    
    return list(invoice_groups.values())

def load_downloaded_log():
    """Load the log of already downloaded files"""
    log_file = "downloaded_invoices_log.json"
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_last_downloaded_invoice_number(downloaded_log):
    """Get the highest invoice number that was downloaded"""
    if not downloaded_log:
        return 0
    
    max_invoice_number = 0
    for entry in downloaded_log:
        try:
            invoice_number = int(entry.get("invoice_number", "0"))
            max_invoice_number = max(max_invoice_number, invoice_number)
        except (ValueError, TypeError):
            continue
    
    return max_invoice_number

def filter_new_invoices(filtered_invoices, last_downloaded_number):
    """Filter invoices to only include those newer than the last downloaded"""
    if last_downloaded_number == 0:
        return filtered_invoices
    
    new_invoices = []
    for invoice in filtered_invoices:
        try:
            invoice_number = int(invoice.get("invoice_number", "0"))
            if invoice_number > last_downloaded_number:
                new_invoices.append(invoice)
        except (ValueError, TypeError):
            # If invoice number is not a valid integer, include it to be safe
            new_invoices.append(invoice)
    
    return new_invoices

def save_downloaded_log(downloaded_log):
    """Save the log of downloaded files"""
    log_file = "downloaded_invoices_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(downloaded_log, f, indent=2, ensure_ascii=False)

def download_invoice(invoice_link, filename, downloads_folder):
    """Download a single invoice file"""
    try:
        print(f"⬇️  Downloading: {filename}")
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(invoice_link, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save the file
        file_path = os.path.join(downloads_folder, filename)
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {filename} ({len(response.content)} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def main():
    """Main function to download all invoices"""
    print("🚀 Starting invoice download process...")
    
    # Load invoice links
    try:
        with open("invoice_links.json", "r", encoding="utf-8") as f:
            invoice_data = json.load(f)
    except FileNotFoundError:
        print("❌ invoice_links.json not found!")
        return
    except json.JSONDecodeError:
        print("❌ Error reading invoice_links.json!")
        return
    
    if not invoice_data:
        print("📭 No invoice links found in the file.")
        return
    
    # Filter to keep only the latest invoice for each invoice number
    print(f"📊 Found {len(invoice_data)} total invoice links")
    filtered_invoices = filter_latest_invoices(invoice_data)
    print(f"📋 After filtering duplicates: {len(filtered_invoices)} unique invoices")
    
    # Create downloads folder
    downloads_folder = create_downloads_folder()
    
    # Load download log and find last downloaded invoice
    downloaded_log = load_downloaded_log()
    last_downloaded_number = get_last_downloaded_invoice_number(downloaded_log)
    
    if last_downloaded_number > 0:
        print(f"🔍 Last downloaded invoice: {last_downloaded_number}")
        # Filter to only include invoices newer than the last downloaded
        new_invoices = filter_new_invoices(filtered_invoices, last_downloaded_number)
        print(f"📋 New invoices to download: {len(new_invoices)} (invoice numbers > {last_downloaded_number})")
        filtered_invoices = new_invoices
    else:
        print("📋 No previous downloads found - will download all invoices")
    
    if not filtered_invoices:
        print("✅ All invoices are already downloaded!")
        return
    
    downloaded_invoice_numbers = {entry.get("invoice_number") for entry in downloaded_log}
    
    # Process each invoice
    new_downloads = 0
    skipped_duplicates = 0
    failed_downloads = 0
    
    for i, invoice in enumerate(filtered_invoices, 1):
        invoice_link = invoice.get("invoice_link", "")
        order_id = invoice.get("order_id", "unknown")
        invoice_number = invoice.get("invoice_number", "unknown")
        
        print(f"\n[{i}/{len(filtered_invoices)}] Processing Order {order_id}, Invoice {invoice_number}")
        
        # Check if invoice number already downloaded
        if invoice_number in downloaded_invoice_numbers:
            print(f"⏭️  Invoice {invoice_number} already downloaded - skipping")
            skipped_duplicates += 1
            continue
        
        # Generate filename
        filename = get_filename_from_invoice_number(invoice_number)
        file_path = os.path.join(downloads_folder, filename)
        
        # Check if file already exists (additional safety check)
        if os.path.exists(file_path):
            print(f"📁 File already exists - skipping")
            # Add to log if not already there
            if invoice_number not in downloaded_invoice_numbers:
                downloaded_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "order_id": order_id,
                    "invoice_number": invoice_number,
                    "invoice_link": invoice_link,
                    "filename": filename,
                    "status": "already_existed"
                })
                downloaded_invoice_numbers.add(invoice_number)
            skipped_duplicates += 1
            continue
        
        # Download the file
        success = download_invoice(invoice_link, filename, downloads_folder)
        
        if success:
            # Add to download log
            downloaded_log.append({
                "timestamp": datetime.now().isoformat(),
                "order_id": order_id,
                "invoice_number": invoice_number,
                "invoice_link": invoice_link,
                "filename": filename,
                "status": "downloaded"
            })
            downloaded_invoice_numbers.add(invoice_number)
            new_downloads += 1
            
            # Save log after each successful download
            save_downloaded_log(downloaded_log)
            
        else:
            failed_downloads += 1
        
        # Small delay to be respectful to the server
        time.sleep(1)
    
    # Final summary
    print(f"\n🎉 Download process completed!")
    print(f"📥 New downloads: {new_downloads}")
    print(f"⏭️  Skipped duplicates: {skipped_duplicates}")
    print(f"❌ Failed downloads: {failed_downloads}")
    print(f"📁 Files saved in: {downloads_folder}")
    
    if failed_downloads > 0:
        print(f"\n⚠️  {failed_downloads} downloads failed. You can run this script again to retry.")

if __name__ == "__main__":
    main()