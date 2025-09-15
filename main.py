import requests
import json
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
from datetime import date, datetime


def process_order(order):
  prod_list = order["lines"]
  oblio_prod_list = []

  for prod in prod_list:
    assert not prod["discountDetails"][0]["lineItemTyDiscount"]
    quantity = prod["quantity"]
    
    oblio_prod = {
        "name": prod["productName"],
        "price": prod["amount"],
        "measuringUnit": "buc",
        "vatName": "Normala",
        "vatPercentage": 21,
        "vatIncluded": 1,
        "quantity": quantity,
        "discountAllAbove": 1
    }

    prod_discount = {
      "name": "Discount",
      "discount": prod["discountDetails"][0]["lineItemDiscount"] * quantity,
      "discountType": "valoric"
    }

    # must first append the prod
    oblio_prod_list.append(oblio_prod)

    # only after the discount
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

  invoice_payload = {
    "cif": cif,
    "client": {
      "name": client_name,
      "address": client_adress,
      "state": county,
      "city": city,
      "country": "Romania"
    },
    "seriesName": "AAA",
    "products": oblio_prod_list
  }

  with open("current_order.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(invoice_payload))
    
  # now we send the data to oblio
    

  url = "https://www.oblio.eu/api/authorize/token"
  payload = f'client_id={client_id}&client_secret={client_secret}'
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  response_oblio_auth = requests.request("POST", url, headers=headers, data=payload)

  print(response_oblio_auth.text)

  headers = {
    'Authorization': f"Bearer {response_oblio_auth.json()["access_token"]}"
  }

  res = requests.get("https://www.oblio.eu/api/nomenclature/companies", headers=headers)
  print(res.text)

  emitere_factura_url = "https://www.oblio.eu/api/docs/invoice"

  res2 = requests.request("POST", emitere_factura_url, headers=headers, json=invoice_payload)

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

  print(res3.text)
  with open("current_order_trendyol_invoice_link_response.json", "w", encoding="utf-8") as f:
    f.write(res3.text)


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

url = f"https://apigw.trendyol.com/integration/order/sellers/{seller_id}/orders?size=200"


headers = {
  'User-Agent': f'{seller_id} - SelfIntegration',
}

response = requests.request("GET", url, headers=headers, auth=HTTPBasicAuth(api_key, api_secret))

#to file
with open("orders.json", "w", encoding="utf-8") as f:
    f.write(response.text)


data = response.json()
content_list = data["content"]

for order in content_list[0:8]:
  

  if "invoiceLink" not in order.keys():
    start_process_order_with_no_invoice_link(order)
  else:
    print("Has invoice ... Skipping ...")
    