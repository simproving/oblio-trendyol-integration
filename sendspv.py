#!/usr/bin/env python3
"""
Script to send invoices to SPV (Sistema de Prelucrare a Facturilor) using Oblio API.
Usage: python sendspv.py <start_number> <end_number>
"""

import sys
import os
import requests
import json
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    
    cif = os.getenv('CIF')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    
    if not all([cif, client_id, client_secret]):
        raise ValueError("Missing required environment variables: CIF, CLIENT_ID, CLIENT_SECRET")
    
    return cif, client_id, client_secret

def get_access_token(client_id, client_secret):
    """Get access token from Oblio API"""
    url = "https://www.oblio.eu/api/authorize/token"
    
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data.get('access_token')
    
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing token response: {e}")
        return None

def send_invoice_to_spv(access_token, cif, series_name, invoice_number):
    """Send a single invoice to SPV"""
    url = "https://www.oblio.eu/api/docs/einvoice"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    payload = {
        'cif': cif,
        'seriesName': series_name,
        'number': invoice_number
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        
        result = response.json()
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error sending invoice {invoice_number}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing response for invoice {invoice_number}: {e}")
        return None

def main():
    """Main function to process invoice range"""
    if len(sys.argv) != 3:
        print("Usage: python sendspv.py <start_number> <end_number>")
        print("Example: python sendspv.py 100 105")
        sys.exit(1)
    
    try:
        start_number = int(sys.argv[1])
        end_number = int(sys.argv[2])
    except ValueError:
        print("Error: Start and end numbers must be integers")
        sys.exit(1)
    
    if start_number > end_number:
        print("Error: Start number must be less than or equal to end number")
        sys.exit(1)
    
    if start_number <= 4000:
        print("Error: Invoice numbers must be over 4000")
        sys.exit(1)
    
    if end_number <= 4000:
        print("Error: Invoice numbers must be over 4000")
        sys.exit(1)
    
    # Load environment variables
    try:
        cif, client_id, client_secret = load_environment()
        print(f"Using CIF: {cif}")
    except ValueError as e:
        print(f"Environment error: {e}")
        sys.exit(1)
    
    # Get access token
    print("Getting access token...")
    access_token = get_access_token(client_id, client_secret)
    if not access_token:
        print("Failed to get access token")
        sys.exit(1)
    
    print("Access token obtained successfully")
    
    # Default series name (you may need to adjust this based on your invoices)
    series_name = "AAA"  # Change this to match your invoice series
    
    # Process invoices in the range
    successful_sends = 0
    failed_sends = 0
    
    print(f"\nSending invoices {start_number} to {end_number} to SPV...")
    print("-" * 50)
    
    for invoice_number in range(start_number, end_number + 1):
        print(f"Processing invoice {series_name}-{invoice_number}...", end=" ")
        
        result = send_invoice_to_spv(access_token, cif, series_name, invoice_number)
        
        if result and result.get('status') == 200:
            data = result.get('data', {})
            text = data.get('text', '')
            
            # Check for success indicators
            if (data.get('sent') == True or 
                'trimisa cu succes' in text.lower() or 
                'factura a fost trimisa in spv' in text.lower()):
                print("✓ SUCCESS")
                successful_sends += 1
            else:
                print(f"✗ FAILED: {text}")
                print(f"Exiting after failure on invoice {invoice_number}")
                sys.exit(1)
        else:
            print("✗ FAILED: API error")
            print(f"Exiting after failure on invoice {invoice_number}")
            sys.exit(1)
    
    # Summary
    print("-" * 50)
    print(f"Summary:")
    print(f"  Successful sends: {successful_sends}")

if __name__ == "__main__":
    main()