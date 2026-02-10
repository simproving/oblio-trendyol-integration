import requests
import json
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
from datetime import date, datetime
import time


def process_order(order):
  prod_list = order["lines"]
  oblio_prod_list = []

  for prod in prod_list:
    assert not prod["discountDetails"][0]["lineItemTyDiscount"]
    quantity = prod["quantity"]
    
    oblio_prod = {
        "name": prod["productName"],
        "code": prod["productCode"],
        "price": prod["amount"],
        "measuringUnit": "buc",
        "vatName": "Normala",
        "vatPercentage": 21,
        "vatIncluded": 1,
        "quantity": quantity,
        "discountAllAbove": 1
    }

    #discount_value = prod["discountDetails"][0]["lineItemDiscount"]
    discount_value = prod["discount"]

    prod_discount = {
      "name": "Discount",
      "discount": discount_value * quantity,
      "discountType": "valoric"
    }

    # must first append the prod
    oblio_prod_list.append(oblio_prod)

    # only after the discount
    if discount_value:
      oblio_prod_list.append(prod_discount)
  
  return oblio_prod_list


def start_process_order_with_no_invoice_link(order):
  shipment_package_id = order["id"]

  # get the invoice data from order
  oblio_prod_list = process_order(order)

  invoice_address = order["invoiceAddress"]
  client_name = invoice_address["firstName"] + " " + invoice_address["lastName"]
  client_adress = invoice_address["address1"] + " " + invoice_address["address2"]
  county = invoice_address["countyName"]
  city = invoice_address["city"]
  customer_id = order["customerId"]
  county_id = invoice_address["countyId"]
  postal_code = invoice_address["postalCode"]
  
  # Handle Bucharest sectors based on postal code
  if county_id == 12261437:
    print("Bucharest postal code")
    sector_digit = postal_code[:2]
    if sector_digit in ["01", "02", "03", "04", "05", "06"]:
      sector_number = int(sector_digit)
      city = f"Sector {sector_number}"

  invoice_payload = {
    "cif": cif,
    "client": {
      "name": client_name,
      "address": client_adress,
      "state": county,
      "city": city,
      "country": "Romania",
      "save": 1,
      "code": customer_id
    },
    "seriesName": "AAA",
    "products": oblio_prod_list
  }

  with open("current_order.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(invoice_payload))
    
  # now we send the data to oblio

  headers = {
    'Authorization': f"Bearer {response_oblio_auth.json()["access_token"]}"
  }

  emitere_factura_url = "https://www.oblio.eu/api/docs/invoice"

  res2 = requests.request("POST", emitere_factura_url, headers=headers, json=invoice_payload)

  if res2.status_code == 429:
    print("Too many requests, sleeping for 60s...")
    time.sleep(60)
    res2 = requests.request("POST", emitere_factura_url, headers=headers, json=invoice_payload)

  if res2.status_code == 200:
    print("Success: Factura emisa")
  else:
    print(res2.status_code)
    print(res2.text)
    exit("Exiting ... Eroare emitere factura")

  print(res2.text)

  with open("current_order_oblio_response.json", "w", encoding="utf-8") as f:
    f.write(res2.text)

  # now we send the invoive link to trendyol

  oblio_response = res2.json()
  invoice_link = oblio_response["data"]["link"]
  invoice_number = oblio_response["data"]["number"]
  total_amount = oblio_response["data"]["total"]

  # Get Trendyol total price for comparison
  trendyol_total_price = order["totalPrice"]
  oblio_total_price = float(total_amount)
  
  # Price validation check
  print(f"\n=== PRICE VALIDATION ===")
  print(f"Trendyol Total: {trendyol_total_price} RON")
  print(f"Oblio Total: {oblio_total_price} RON")
  
  price_difference = abs(trendyol_total_price - oblio_total_price)
  if price_difference < 0.01:  # Allow for small floating point differences
    print("✅ PRICES MATCH!")
  else:
    print(f"❌ PRICE MISMATCH! Difference: {price_difference:.2f} RON")
    exit("Price match fail")
  print("========================\n")

  # Save invoice link to persistent file
  save_invoice_link(shipment_package_id, invoice_link, invoice_number, total_amount)

  print(invoice_link)

  send_invoice_link_url = f"https://apigw.trendyol.com/integration/sellers/{seller_id}/seller-invoice-links"
  print(send_invoice_link_url)

  send_invoice_link_payload = {
    "invoiceLink": invoice_link,
    "shipmentPackageId": shipment_package_id
  }
  headers = {
  'User-Agent': f'{seller_id} - SelfIntegration',
  }

  res3 = requests.request("POST", send_invoice_link_url, headers=headers, json=send_invoice_link_payload, auth=HTTPBasicAuth(api_key, api_secret))
  print(f"Send invoice link trendyol response status code: {res3.status_code}")
  if res3.status_code == 201:
    print("Success: Send invoice link to trendyol")
  else:
    exit(" ====> Error sending invoice link to trendyol !!! <====")

  print(res3.text)
  with open("current_order_trendyol_invoice_link_response.json", "w", encoding="utf-8") as f:
    f.write(res3.text)


def save_cancelled_order(order, reason):
  """Save cancelled order information to a persistent file"""
  order_id = order.get("id", "Unknown")
  
  # Load existing cancelled orders or create new list
  cancelled_orders_file = "cancelled_orders_info.json"
  try:
    with open(cancelled_orders_file, "r", encoding="utf-8") as f:
      cancelled_orders = json.load(f)
  except FileNotFoundError:
    cancelled_orders = []
  
  # Check if order ID already exists
  existing_order_ids = [existing_order.get("order_id") for existing_order in cancelled_orders]
  if order_id in existing_order_ids:
    print(f"🔄 Order {order_id} already exists in cancelled orders file - skipping duplicate")
    return
  
  cancelled_order_data = {
    "timestamp": datetime.now().isoformat(),
    "order_id": order_id,
    "order_number": order.get("orderNumber", "Unknown"),
    "cancellation_reason": reason,
    "total_price": order.get("totalPrice", 0),
    "gross_amount": order.get("grossAmount", 0),
    "customer_name": "",
    "order_date": order.get("orderDate", ""),
    "lines": []
  }
  
  # Extract customer name from invoice address
  invoice_address = order.get("invoiceAddress", {})
  if invoice_address:
    cancelled_order_data["customer_name"] = f"{invoice_address.get('firstName', '')} {invoice_address.get('lastName', '')}".strip()
  
  # Extract product information
  for line in order.get("lines", []):
    line_info = {
      "product_name": line.get("productName", ""),
      "quantity": line.get("quantity", 0),
      "price": line.get("price", 0),
      "amount": line.get("amount", 0),
      "status": line.get("orderLineItemStatusName", "")
    }
    cancelled_order_data["lines"].append(line_info)
  
  # Add new cancelled order
  cancelled_orders.append(cancelled_order_data)
  
  # Save back to file
  with open(cancelled_orders_file, "w", encoding="utf-8") as f:
    json.dump(cancelled_orders, f, indent=2, ensure_ascii=False)
  
  print(f"💾 Saved cancelled order info for order {order_id}")


def should_skip_order(order):
  """Check if order should be skipped based on status"""
  # Check line item statuses
  for line in order.get("lines", []):
    line_status = line.get("orderLineItemStatusName", "")
    if line_status == "Cancelled":
      return True, f"Line item status: {line_status}", True  # True indicates it's cancelled
    elif line_status == "Awaiting":
      return True, f"Line item status: {line_status}", False  # False indicates it's not cancelled
  
  # Check package history for latest status
  package_histories = order.get("packageHistories", [])
  if package_histories:
    # Get the latest status (last item in the list)
    latest_status = package_histories[-1].get("status", "")
    if latest_status == "Cancelled":
      return True, f"Package status: {latest_status}", True  # True indicates it's cancelled
    elif latest_status == "Awaiting":
      return True, f"Package status: {latest_status}", False  # False indicates it's not cancelled
  
  return False, "", False


def save_invoice_link(order_id, invoice_link, invoice_number, total_amount):
  """Save invoice link to a persistent file with order details"""
  invoice_data = {
    "timestamp": datetime.now().isoformat(),
    "order_id": order_id,
    "invoice_number": invoice_number,
    "invoice_link": invoice_link,
    "total_amount": total_amount
  }
  
  # Load existing invoice links or create new list
  invoice_links_file = "invoice_links.json"
  try:
    with open(invoice_links_file, "r", encoding="utf-8") as f:
      invoice_links = json.load(f)
  except FileNotFoundError:
    invoice_links = []
  
  # Add new invoice link
  invoice_links.append(invoice_data)
  
  # Save back to file
  with open(invoice_links_file, "w", encoding="utf-8") as f:
    json.dump(invoice_links, f, indent=2, ensure_ascii=False)
  
  print(f"Saved invoice link for order {order_id}: {invoice_link}")

########################################### START ###########################################

load_dotenv()
seller_id = os.getenv("SELLER_ID")
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
cif = os.getenv("CIF")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Oblio auth
url = "https://www.oblio.eu/api/authorize/token"
payload = f'client_id={client_id}&client_secret={client_secret}'
headers = {
  'Content-Type': 'application/x-www-form-urlencoded'
}

response_oblio_auth = requests.request("POST", url, headers=headers, data=payload)

if response_oblio_auth.status_code == 200:
  print("Success: Oblio auth")
else:
  exit("Oblio auth fail")

print(response_oblio_auth.text)

# Get orders trendyol
url = f"https://apigw.trendyol.com/integration/order/sellers/{seller_id}/orders?size=200"

headers = {
  'User-Agent': f'{seller_id} - SelfIntegration',
}

response = requests.request("GET", url, headers=headers, auth=HTTPBasicAuth(api_key, api_secret))
if response.status_code == 200:
  print("Success: Get trendyol orders")

#to file
with open("orders.json", "w", encoding="utf-8") as f:
    f.write(response.text)


data = response.json()
content_list = data["content"]

for order in content_list:
  order_id = order.get("id", "Unknown")
  
  # Check if order should be skipped due to status
  should_skip, skip_reason, is_cancelled = should_skip_order(order)
  if should_skip:
    print(f"⏭️  Skipping order {order_id}: {skip_reason}")
    
    # If it's a cancelled order, save the order info
    if is_cancelled:
      save_cancelled_order(order, skip_reason)
    
    continue
  
  if "invoiceLink" not in order.keys():
    print(f"📋 Processing order {order_id}")
    
    start_process_order_with_no_invoice_link(order)
    #break # we only do 1 at a time for now
    time.sleep(1)
  else:
    print(f"✅ Order {order_id} already has invoice ... Skipping ...")
  
    