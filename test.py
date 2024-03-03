import requests
import json

import secrets
import string
import time

def generate_token(length=40):
    alphabet = string.ascii_letters + string.digits
    timestamp = str(int(time.time() * 1000))  # Get current time in milliseconds since epoch and convert to string
    random_chars_length = length - len(timestamp)
    random_chars = ''.join(secrets.choice(alphabet) for _ in range(random_chars_length))
    return timestamp + random_chars

def put_stocks(props):

    data = get_all()
    #post - modify a stock that already exist in the database
    if props["action"] == "modify":
        for item in data:
            if item["ticker"] == props["selectedStock"]:
                dict_post = {
                    "stock_id": item["stock_id"],
                    "portfolio_id": item["portfolio_id"],
                    "user_id": item["user_id"],
                    "user_name":item["user_name"],
                    "ticker": item["ticker"],
                    "quantity": props["quantity"],
                    "purchase_price": item["purchase_price"]
                }
                break

    #put - create a new object in the database
    else:
        portfolio_id = "91474d3a-2bcd-4638-985d-089680444d55"
        user_id = "61480832-0556-4176-8a20-f491f2597e96"
        user_name= "Ignacio Trullenque"
        dict_post = {
                    "stock_id": "17095042007310IxLhG8qXUfwtW3cjpO3M8sX6dK",#generate_token(),
                    "portfolio_id": portfolio_id,
                    "user_id": user_id,
                    "user_name":user_name,
                    "ticker": props["selectedStock"],
                    "quantity": props["quantity"],
                    "purchase_price": 0
                }
    
    if dict_post:
        json_data = json.dumps(dict_post)
        stock_id = dict_post["stock_id"]
        try:
            url = f"https://g71ab6e0bc037e1-stocktrackerdb.adb.eu-madrid-1.oraclecloudapps.com/ords/admin/user_stocks/{stock_id}"
            response = requests.put(url,data=json_data,headers={"Content-Type": "application/json"})

            if response.status_code == 200:
                return "Stock modified correctly", 200
            else:
                return f"Failed to modify stock. Status code: {response.status_code}", response.reason
        except Exception as e:
            print(f"Error: {str(e)}")

def get_all():

    try:
        url = "https://g71ab6e0bc037e1-stocktrackerdb.adb.eu-madrid-1.oraclecloudapps.com/ords/admin/user_stocks/" 
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"])>0:
                return data["items"]
            else:
                raise Exception("Data no found in stock databases")
        else:
            response.raise_for_status()
    
    except Exception as e:
        print("Error:", str(e))
    
    return []

props ={"action":"create","selectedStock":"NVDA","quantity":10}
result = put_stocks(props)