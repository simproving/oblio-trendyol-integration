#!/usr/bin/env python3
"""
Test script specifically for Bucharest sector handling logic
Tests various scenarios to ensure the city is correctly set to the sector
"""

import json
import re


def test_bucharest_sector_logic(invoice_address, expected_city):
    """Test the Bucharest sector logic with given parameters"""
    
    # Original city from the address
    original_city = invoice_address.get("city", "")
    city = original_city  # Start with original city
    
    # Apply the Bucharest sector logic (copied from main.py)
    county_id = invoice_address.get("countyId", 0)
    postal_code = invoice_address.get("postalCode", "")
    
    # Handle Bucharest sectors based on postal code
    if county_id == 12261437:
        sector_digit = postal_code[:2]
        if sector_digit in ["01", "02", "03", "04", "05", "06"]:
            sector_number = int(sector_digit)
            city = f"Sector {sector_number}"
    
    return city, original_city


def create_test_cases():
    """Create comprehensive test cases for Bucharest sector logic"""
    
    test_cases = [
        # Valid Bucharest cases with county ID 12261437
        {
            "name": "Bucharest Sector 1 - Standard",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "010001"},
            "expected_city": "Sector 1"
        },
        {
            "name": "Bucharest Sector 2 - Standard", 
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "020001"},
            "expected_city": "Sector 2"
        },
        {
            "name": "Bucharest Sector 3 - Standard",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "030001"},
            "expected_city": "Sector 3"
        },
        {
            "name": "Bucharest Sector 4 - Standard",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "040001"}, 
            "expected_city": "Sector 4"
        },
        {
            "name": "Bucharest Sector 5 - Standard",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "050001"},
            "expected_city": "Sector 5"
        },
        {
            "name": "Bucharest Sector 6 - Standard",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "060001"},
            "expected_city": "Sector 6"
        },
        
        # Different city name variations (should still work with correct county ID)
        {
            "name": "Bucuresti (no diacritics) - correct county ID",
            "invoice_address": {"city": "Bucuresti", "countyId": 12261437, "postalCode": "010001"},
            "expected_city": "Sector 1"
        },
        {
            "name": "BUCURESTI (uppercase) - correct county ID",
            "invoice_address": {"city": "BUCURESTI", "countyId": 12261437, "postalCode": "030001"},
            "expected_city": "Sector 3"
        },
        
        # Edge cases that should NOT trigger sector conversion
        {
            "name": "Invalid sector 7 (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "070001"},
            "expected_city": "București"  # Should remain original
        },
        {
            "name": "Invalid sector 8 (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "080001"},
            "expected_city": "București"  # Should remain original
        },
        {
            "name": "Invalid sector 9 (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "090001"},
            "expected_city": "București"  # Should remain original
        },
        {
            "name": "Short postal code (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "01001"},  # 5 digits
            "expected_city": "București"  # Should remain original
        },
        {
            "name": "Long postal code (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": "0100001"},  # 7 digits
            "expected_city": "București"  # Should remain original
        },
        {
            "name": "No postal code (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437},  # No postalCode
            "expected_city": "București"  # Should remain original
        },
        {
            "name": "Empty postal code (should not convert)",
            "invoice_address": {"city": "București", "countyId": 12261437, "postalCode": ""},
            "expected_city": "București"  # Should remain original
        },
        
        # Wrong county ID (should not convert even with valid postal codes)
        {
            "name": "Cluj county ID (should not convert)",
            "invoice_address": {"city": "Cluj-Napoca", "countyId": 12261440, "postalCode": "010001"},
            "expected_city": "Cluj-Napoca"  # Should remain original
        },
        {
            "name": "Ilfov county ID (should not convert)",
            "invoice_address": {"city": "Voluntari", "countyId": 12261449, "postalCode": "010001"},
            "expected_city": "Voluntari"  # Should remain original
        },
        {
            "name": "Bucharest city but wrong county ID (should not convert)",
            "invoice_address": {"city": "București", "countyId": 99999999, "postalCode": "010001"},
            "expected_city": "București"  # Should remain original
        }
    ]
    
    return test_cases


def run_bucharest_tests():
    """Run all Bucharest sector tests"""
    
    print("🏛️  BUCHAREST SECTOR LOGIC TESTS")
    print("=" * 60)
    
    test_cases = create_test_cases()
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test {i+1}: {test_case['name']}")
        
        result_city, original_city = test_bucharest_sector_logic(
            test_case["invoice_address"],
            test_case["expected_city"]
        )
        
        expected = test_case["expected_city"]
        
        print(f"   County ID: {test_case['invoice_address'].get('countyId', 'N/A')}")
        print(f"   Original City: {original_city}")
        print(f"   Postal Code: {test_case['invoice_address'].get('postalCode', 'N/A')}")
        print(f"   Expected: {expected}")
        print(f"   Result: {result_city}")
        
        if result_city == expected:
            print(f"   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/len(test_cases)*100):.1f}%")
    
    return failed == 0


def test_real_orders_bucharest():
    """Test Bucharest logic on real orders from orders.json"""
    
    print(f"\n🏛️  TESTING REAL BUCHAREST ORDERS")
    print("=" * 60)
    
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        orders = data.get("content", [])
    except FileNotFoundError:
        print("❌ orders.json not found")
        return
    
    bucharest_orders = []
    
    # Find orders with Bucharest addresses (county ID 12261437)
    for order in orders:
        invoice_address = order.get("invoiceAddress", {})
        county_id = invoice_address.get("countyId", 0)
        
        # Check if it's a Bucharest order
        if county_id == 12261437:
            bucharest_orders.append(order)
    
    print(f"📊 Found {len(bucharest_orders)} Bucharest orders")
    
    if not bucharest_orders:
        print("ℹ️  No Bucharest orders found in orders.json")
        return
    
    # Test each Bucharest order
    for i, order in enumerate(bucharest_orders):
        order_id = order.get("id", "Unknown")
        invoice_address = order.get("invoiceAddress", {})
        county_id = invoice_address.get("countyId", 0)
        county_name = invoice_address.get("countyName", "")
        original_city = invoice_address.get("city", "")
        postal_code = invoice_address.get("postalCode", "")
        
        print(f"\n📦 Order {i+1}: {order_id}")
        print(f"   County ID: {county_id}")
        print(f"   County Name: {county_name}")
        print(f"   Original City: {original_city}")
        print(f"   Postal Code: {postal_code}")
        
        # Apply the logic
        result_city, _ = test_bucharest_sector_logic(invoice_address, "")
        
        print(f"   Result City: {result_city}")
        
        # Check if conversion happened
        if result_city.startswith("Sector "):
            print(f"   ✅ Successfully converted to {result_city}")
        else:
            print(f"   ℹ️  No conversion (reason: invalid postal code or sector)")
        
        # Show customer info
        customer_name = f"{order.get('customerFirstName', '')} {order.get('customerLastName', '')}".strip()
        print(f"   Customer: {customer_name}")


def main():
    """Main function"""
    print("🧪 BUCHAREST SECTOR TESTING SUITE")
    print("=" * 60)
    
    # Run synthetic tests
    success = run_bucharest_tests()
    
    # Test real orders
    test_real_orders_bucharest()
    
    if success:
        print(f"\n🎉 All synthetic tests passed!")
    else:
        print(f"\n❌ Some synthetic tests failed!")


if __name__ == "__main__":
    main()