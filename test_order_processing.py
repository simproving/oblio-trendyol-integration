#!/usr/bin/env python3
"""
Test script for order processing logic
Tests the processing functions on orders from orders.json without making API calls
"""

import json
import sys
from datetime import datetime
from main import process_order, should_skip_order, save_cancelled_order


def load_orders():
    """Load orders from orders.json file"""
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("content", [])
    except FileNotFoundError:
        print("❌ orders.json not found. Run main.py first to fetch orders.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing orders.json: {e}")
        return []


def test_process_order(order):
    """Test the process_order function on a single order"""
    print(f"\n🧪 Testing process_order for order {order.get('id', 'Unknown')}")
    
    try:
        oblio_prod_list = process_order(order)
        
        print(f"✅ Successfully processed order")
        print(f"   Products generated: {len(oblio_prod_list)}")
        
        # Show product details
        for i, prod in enumerate(oblio_prod_list):
            if "name" in prod and prod["name"] != "Discount":
                print(f"   Product {i+1}: {prod['name'][:50]}...")
                print(f"     Price: {prod['price']} RON, Quantity: {prod['quantity']}")
            elif prod.get("name") == "Discount":
                print(f"   Discount: {prod['discount']} RON")
        
        return True, oblio_prod_list
        
    except Exception as e:
        print(f"❌ Error processing order: {e}")
        return False, None


def test_should_skip_order(order):
    """Test the should_skip_order function"""
    order_id = order.get('id', 'Unknown')
    print(f"\n🔍 Testing should_skip_order for order {order_id}")
    
    should_skip, reason, is_cancelled = should_skip_order(order)
    
    if should_skip:
        status_type = "CANCELLED" if is_cancelled else "AWAITING"
        print(f"   ⏭️  Should skip: {reason} ({status_type})")
    else:
        print(f"   ✅ Should process: Order is ready")
    
    return should_skip, reason, is_cancelled


def test_invoice_payload_generation(order):
    """Test the complete invoice payload generation"""
    print(f"\n📋 Testing invoice payload generation for order {order.get('id', 'Unknown')}")
    
    try:
        # Process the order
        oblio_prod_list = process_order(order)
        
        # Generate invoice payload (similar to main.py logic)
        invoice_address = order["invoiceAddress"]
        client_name = invoice_address["firstName"] + " " + invoice_address["lastName"]
        client_address = invoice_address["address1"] + " " + invoice_address["address2"]
        county = invoice_address["countyName"]
        city = invoice_address["city"]
        customer_id = order["customerId"]
        
        # Handle Bucharest sectors based on county ID
        county_id = invoice_address.get("countyId", 0)
        postal_code = invoice_address.get("postalCode", "")
        
        if county_id == 12261437:
            sector_digit = postal_code[:2]
            if sector_digit in ["01", "02", "03", "04", "05", "06"]:
                sector_number = int(sector_digit)
                city = f"Sector {sector_number}"
        
        invoice_payload = {
            "cif": "TEST_CIF",  # Using test value
            "client": {
                "name": client_name,
                "address": client_address,
                "state": county,
                "city": city,
                "country": "Romania",
                "save": 1,
                "code": customer_id
            },
            "seriesName": "AAA",
            "products": oblio_prod_list
        }
        
        print(f"✅ Invoice payload generated successfully")
        print(f"   Client: {client_name}")
        print(f"   Address: {client_address}")
        print(f"   City: {city}, County: {county}")
        print(f"   Products: {len(oblio_prod_list)} items")
        
        # Calculate totals
        total_amount = 0
        total_discount = 0
        for prod in oblio_prod_list:
            if prod.get("name") != "Discount":
                total_amount += prod.get("price", 0) * prod.get("quantity", 1)
            else:
                total_discount += prod.get("discount", 0)
        
        final_total = total_amount - total_discount
        trendyol_total = order.get("totalPrice", 0)
        
        print(f"   Calculated total: {final_total:.2f} RON")
        print(f"   Trendyol total: {trendyol_total:.2f} RON")
        
        price_diff = abs(final_total - trendyol_total)
        if price_diff < 0.01:
            print(f"   ✅ Price validation: MATCH")
        else:
            print(f"   ❌ Price validation: MISMATCH (diff: {price_diff:.2f} RON)")
        
        return True, invoice_payload
        
    except Exception as e:
        print(f"❌ Error generating invoice payload: {e}")
        return False, None


def run_comprehensive_test():
    """Run comprehensive tests on all orders"""
    print("🚀 Starting comprehensive order processing tests")
    print("=" * 60)
    
    orders = load_orders()
    if not orders:
        return
    
    print(f"📊 Loaded {len(orders)} orders from orders.json")
    
    # Statistics
    stats = {
        "total_orders": len(orders),
        "processable_orders": 0,
        "skipped_orders": 0,
        "cancelled_orders": 0,
        "awaiting_orders": 0,
        "orders_with_invoice": 0,
        "processing_errors": 0,
        "price_mismatches": 0
    }
    
    for i, order in enumerate(orders):
        order_id = order.get('id', 'Unknown')
        print(f"\n{'='*60}")
        print(f"📦 Order {i+1}/{len(orders)}: {order_id}")
        print(f"   Order Number: {order.get('orderNumber', 'Unknown')}")
        print(f"   Total Price: {order.get('totalPrice', 0)} RON")
        print(f"   Status: {order.get('status', 'Unknown')}")
        
        # Check if order has invoice link
        if "invoiceLink" in order:
            print(f"   ✅ Already has invoice link")
            stats["orders_with_invoice"] += 1
            continue
        
        # Test skip logic
        should_skip, reason, is_cancelled = test_should_skip_order(order)
        if should_skip:
            stats["skipped_orders"] += 1
            if is_cancelled:
                stats["cancelled_orders"] += 1
            else:
                stats["awaiting_orders"] += 1
            continue
        
        # Test processing
        stats["processable_orders"] += 1
        success, oblio_products = test_process_order(order)
        if not success:
            stats["processing_errors"] += 1
            continue
        
        # Test invoice payload generation
        success, invoice_payload = test_invoice_payload_generation(order)
        if not success:
            stats["processing_errors"] += 1
            continue
        
        # Check for price mismatches
        if invoice_payload:
            total_amount = 0
            total_discount = 0
            for prod in invoice_payload["products"]:
                if prod.get("name") != "Discount":
                    total_amount += prod.get("price", 0) * prod.get("quantity", 1)
                else:
                    total_discount += prod.get("discount", 0)
            
            final_total = total_amount - total_discount
            trendyol_total = order.get("totalPrice", 0)
            price_diff = abs(final_total - trendyol_total)
            
            if price_diff >= 0.01:
                stats["price_mismatches"] += 1
    
    # Print final statistics
    print(f"\n{'='*60}")
    print("📊 FINAL TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total orders: {stats['total_orders']}")
    print(f"Orders with existing invoice: {stats['orders_with_invoice']}")
    print(f"Skipped orders: {stats['skipped_orders']}")
    print(f"  - Cancelled: {stats['cancelled_orders']}")
    print(f"  - Awaiting: {stats['awaiting_orders']}")
    print(f"Processable orders: {stats['processable_orders']}")
    print(f"Processing errors: {stats['processing_errors']}")
    print(f"Price mismatches: {stats['price_mismatches']}")
    
    success_rate = ((stats['processable_orders'] - stats['processing_errors']) / max(stats['processable_orders'], 1)) * 100
    print(f"\nProcessing success rate: {success_rate:.1f}%")


def test_specific_order(order_id):
    """Test processing for a specific order ID"""
    print(f"🎯 Testing specific order: {order_id}")
    
    orders = load_orders()
    if not orders:
        return
    
    # Find the order
    target_order = None
    for order in orders:
        if str(order.get('id', '')) == str(order_id):
            target_order = order
            break
    
    if not target_order:
        print(f"❌ Order {order_id} not found in orders.json")
        return
    
    print(f"✅ Found order {order_id}")
    print(f"   Order Number: {target_order.get('orderNumber', 'Unknown')}")
    print(f"   Customer: {target_order.get('customerFirstName', '')} {target_order.get('customerLastName', '')}")
    print(f"   Total Price: {target_order.get('totalPrice', 0)} RON")
    
    # Run all tests on this order
    test_should_skip_order(target_order)
    test_process_order(target_order)
    test_invoice_payload_generation(target_order)


def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        # Test specific order
        order_id = sys.argv[1]
        test_specific_order(order_id)
    else:
        # Run comprehensive test
        run_comprehensive_test()


if __name__ == "__main__":
    main()