#!/usr/bin/env python3
"""
Interactive test script for order processing
Allows you to interactively test individual orders or browse through them
"""

import json
import sys
from main import process_order, should_skip_order


def load_orders():
    """Load orders from orders.json file"""
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("content", [])
    except FileNotFoundError:
        print("❌ orders.json not found. Run main.py first to fetch orders.")
        return []


def display_order_summary(order, index=None):
    """Display a summary of an order"""
    order_id = order.get('id', 'Unknown')
    order_number = order.get('orderNumber', 'Unknown')
    customer_name = f"{order.get('customerFirstName', '')} {order.get('customerLastName', '')}".strip()
    total_price = order.get('totalPrice', 0)
    status = order.get('status', 'Unknown')
    has_invoice = "invoiceLink" in order
    
    prefix = f"[{index+1}] " if index is not None else ""
    print(f"{prefix}Order {order_id} | {order_number}")
    print(f"    Customer: {customer_name}")
    print(f"    Total: {total_price} RON | Status: {status}")
    print(f"    Has Invoice: {'✅' if has_invoice else '❌'}")
    
    # Show products
    lines = order.get('lines', [])
    print(f"    Products ({len(lines)}):")
    for line in lines[:2]:  # Show first 2 products
        product_name = line.get('productName', 'Unknown')[:40]
        quantity = line.get('quantity', 0)
        price = line.get('price', 0)
        print(f"      - {product_name}... (Qty: {quantity}, Price: {price} RON)")
    
    if len(lines) > 2:
        print(f"      ... and {len(lines) - 2} more products")


def test_order_interactive(order):
    """Interactively test an order"""
    order_id = order.get('id', 'Unknown')
    print(f"\n{'='*60}")
    print(f"🧪 TESTING ORDER {order_id}")
    print(f"{'='*60}")
    
    display_order_summary(order)
    
    print(f"\n🔍 Checking if order should be skipped...")
    should_skip, reason, is_cancelled = should_skip_order(order)
    
    if should_skip:
        status_type = "CANCELLED" if is_cancelled else "AWAITING"
        print(f"⏭️  Order should be SKIPPED: {reason} ({status_type})")
        return
    
    print(f"✅ Order is ready for processing")
    
    if "invoiceLink" in order:
        print(f"ℹ️  Order already has invoice link: {order['invoiceLink']}")
        return
    
    print(f"\n📋 Testing order processing...")
    try:
        oblio_prod_list = process_order(order)
        print(f"✅ Order processed successfully!")
        print(f"   Generated {len(oblio_prod_list)} Oblio products")
        
        # Show details
        total_amount = 0
        total_discount = 0
        
        print(f"\n📦 Product Details:")
        for i, prod in enumerate(oblio_prod_list):
            if prod.get("name") != "Discount":
                print(f"   {i+1}. {prod['name'][:50]}...")
                print(f"      Price: {prod['price']} RON x {prod['quantity']}")
                total_amount += prod['price'] * prod['quantity']
            else:
                print(f"   {i+1}. Discount: -{prod['discount']} RON")
                total_discount += prod['discount']
        
        final_total = total_amount - total_discount
        trendyol_total = order.get("totalPrice", 0)
        
        print(f"\n💰 Price Validation:")
        print(f"   Calculated total: {final_total:.2f} RON")
        print(f"   Trendyol total: {trendyol_total:.2f} RON")
        
        price_diff = abs(final_total - trendyol_total)
        if price_diff < 0.01:
            print(f"   ✅ PRICES MATCH!")
        else:
            print(f"   ❌ PRICE MISMATCH! Difference: {price_diff:.2f} RON")
        
    except Exception as e:
        print(f"❌ Error processing order: {e}")
        import traceback
        traceback.print_exc()


def browse_orders():
    """Browse through orders interactively"""
    orders = load_orders()
    if not orders:
        return
    
    print(f"📊 Loaded {len(orders)} orders")
    
    # Filter orders without invoice links
    processable_orders = [order for order in orders if "invoiceLink" not in order]
    print(f"📋 {len(processable_orders)} orders without invoice links")
    
    current_index = 0
    
    while True:
        if current_index >= len(processable_orders):
            print("🏁 Reached end of processable orders")
            break
        
        order = processable_orders[current_index]
        
        print(f"\n{'='*60}")
        print(f"📦 Order {current_index + 1} of {len(processable_orders)}")
        display_order_summary(order)
        
        print(f"\nOptions:")
        print(f"  [t] Test this order")
        print(f"  [n] Next order")
        print(f"  [p] Previous order")
        print(f"  [j] Jump to order number")
        print(f"  [s] Show order details")
        print(f"  [q] Quit")
        
        choice = input("\nChoice: ").lower().strip()
        
        if choice == 't':
            test_order_interactive(order)
            input("\nPress Enter to continue...")
        elif choice == 'n':
            current_index = min(current_index + 1, len(processable_orders) - 1)
        elif choice == 'p':
            current_index = max(current_index - 1, 0)
        elif choice == 'j':
            try:
                jump_to = int(input("Jump to order number (1-{}): ".format(len(processable_orders))))
                if 1 <= jump_to <= len(processable_orders):
                    current_index = jump_to - 1
                else:
                    print("Invalid order number")
            except ValueError:
                print("Please enter a valid number")
        elif choice == 's':
            print(f"\n📋 Full Order Details:")
            print(json.dumps(order, indent=2, ensure_ascii=False))
            input("\nPress Enter to continue...")
        elif choice == 'q':
            break
        else:
            print("Invalid choice")


def main():
    """Main interactive function"""
    print("🧪 Interactive Order Processing Test")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Test specific order ID
        order_id = sys.argv[1]
        orders = load_orders()
        target_order = None
        
        for order in orders:
            if str(order.get('id', '')) == str(order_id):
                target_order = order
                break
        
        if target_order:
            test_order_interactive(target_order)
        else:
            print(f"❌ Order {order_id} not found")
    else:
        # Interactive browsing
        browse_orders()


if __name__ == "__main__":
    main()