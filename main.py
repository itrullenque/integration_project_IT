import requests
import json
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import secrets
import string
import time

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

#General variables
apikey = "VFVETDZPXW4IOBLD"
#Variables to access to the portfolio in Oracle, because still dont have login
portfolio_id = "91474d3a-2bcd-4638-985d-089680444d55"
user_id = "61480832-0556-4176-8a20-f491f2597e96"
user_name= "Ignacio Trullenque"

#Utility function to generate a token every time the user create a new stock.
#I ask chat gpt for this, and also i use the logic of my previous codes of my work.
def generate_token(length=40):
    alphabet = string.ascii_letters + string.digits
    timestamp = str(int(time.time() * 1000))  
    random_chars_length = length - len(timestamp)
    random_chars = ''.join(secrets.choice(alphabet) for _ in range(random_chars_length))
    return timestamp + random_chars

#Get the stock from oracle DB - table: USER_STOCKS
#Is a get all to obtain the whole data.
def get_all():

    try:
        url = "https://g71ab6e0bc037e1-stocktrackerdb.adb.eu-madrid-1.oraclecloudapps.com/ords/admin/user_stocks/" 
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"])>0:
                #if quantity = 0, exclude
                return data["items"]
            else:
                raise Exception("Data no found in stock databases")
        else:
            response.raise_for_status()
    
    except Exception as e:
        print("Error:", str(e))
    
    return []

#Method to make a put-post request to the table USER_STOCKS
#In the rest API of the DB, the POST and PUT works as the same, so i used the same URL to create and modify.
# The logic of wich action need to execute depend of the information privided by the front.
def put_stocks(props):

    data = get_all()
    #post - modify a stock that already exist in the database
    if props["action"] == "modify":
        action = "modifiyed"
        for item in data:
            if item["ticker"] == props["ticker"]:
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
    #Delete method. The rest endpoint dont have a specific one to delete, so im managing add a cero in the quantity or create a new variable of state.
    elif props["action"] == "delete":
        action = "deleted"
        for item in data:
            if item["ticker"] == props["ticker"]:
                dict_post = {
                    "stock_id": item["stock_id"],
                    "portfolio_id": item["portfolio_id"],
                    "user_id": item["user_id"],
                    "user_name":item["user_name"],
                    "ticker": item["ticker"],
                    "quantity": 0,
                    "purchase_price": item["purchase_price"]
                }
                break

    #put - create a new object in the database
    else:
        action = "created"
        dict_post = {
                    "stock_id": generate_token(),
                    "portfolio_id": portfolio_id,
                    "user_id": user_id,
                    "user_name":user_name,
                    "ticker": props["ticker"],
                    "quantity": props["quantity"],
                    "purchase_price": 0
                }
    
    #Preparing the data to make the request to the DB.
    if dict_post:
        json_data = json.dumps(dict_post)
        stock_id = dict_post["stock_id"]
        try:
            url = f"https://g71ab6e0bc037e1-stocktrackerdb.adb.eu-madrid-1.oraclecloudapps.com/ords/admin/user_stocks/{stock_id}"
            response = requests.put(url,data=json_data,headers={"Content-Type": "application/json"})

            if response.status_code == 200:
                return f"Stock {action} successfully", 200
            else:
                return f"Failed to modify stock. Reason: {response.reason}", response.status_code
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        return f"Failed to modify stock"

#Hompage - it render the portfolio
@app.route('/', methods=["GET"])
def homepage():

    client_stocks = get_all()
    stock_dict    = {}
    total_value = 0

    for item in client_stocks:
        stock = item["ticker"]
        #If quantity is cero is suposed to be eliminated
        if item["quantity"] == 0:
            continue

        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={apikey}"
        response = requests.get(url)
        data = response.json()
        stock_dict[item["ticker"]] = {
            "quantity":item["quantity"],
            "purchase_price":item["purchase_price"],
            "price": float(data["Global Quote"]["05. price"]),
            "latest_trading_day": data["Global Quote"]["07. latest trading day"],
            "total_value": round(float(data["Global Quote"]["05. price"])*item["quantity"],2)
        }
        total_value += stock_dict[item["ticker"]]["total_value"] #calculation of the total value of the portfolio 
    
    for stock, value in stock_dict.items():
        stock_dict[stock]["weighted_value"] = round((value["total_value"]/total_value)*100,2) #% of the representation of the stock in the portfolio

    stock_dict["portfolio_value"] = round(total_value,2)
    
    return stock_dict

#Get the last two month by week of the relevant information of the stocks using AlphaVantage for the info.
@app.route('/<ticker>', methods=["GET"])
def ticker_info(ticker):

    try:
        stock = ticker
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={stock}&apikey={apikey}"
        
        response = requests.get(url)
        data = response.json()
        stock_info = data["Weekly Time Series"]
        selected_items = list(stock_info.items())[:10]
        stock_info = dict(selected_items)
        print(stock_info)
        
        return stock_info

    except Exception as e:
        print(str(e)) 

#Extra implementation by me:
#Search bar - if exist a match between the name input by the user and the info od Alphavantage
@app.route('/search/<ticker>', methods=["GET"])
def ticker_search(ticker):

    try:
        stock = ticker
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={stock}&apikey={apikey}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["bestMatches"] != []:
                stock_dict = {}
                for stock in data["bestMatches"]:
                    stock_dict[stock["1. symbol"]] = stock["2. name"]
                
                return stock_dict
            else:
                return "No data available for the request stock"
        else:
            raise Exception("Error obtaining the information of the stocks", "status code {}" .format(response.status_code))

    except Exception as e:
        print(str(e))

#Route to edit the portfolio.
#Create a new stock or modify a previous one in the portfolio
@app.route('/edit_stock', methods=["POST", "OPTIONS"])
@cross_origin()
def edit_portfolio():

    #Logic to manage the user request
    data = request.get_json()   
    if data and "action" in data:
        if data["action"] == "create":
            if data["newStockName"] != "":
                new_data = {
                    "action":data["action"],
                    "ticker":data["newStockName"],
                    "quantity":data["newStockQuantity"]
                }
                response = ticker_search(new_data["ticker"]) #validate if the stock exist in alphavantage
            else:
                return jsonify({"error_code": 400,"message": "Empty ticker"})
        else:
            if data["selectedStock"] != "":
                new_data = {
                    "action":data["action"],
                    "ticker":data["selectedStock"],
                    "quantity":data["quantity"]
                }
                response = ticker_search(new_data["ticker"])
            else:
                return jsonify({"error_code": 201,"message": "Empty ticker"})
            
        #if the stock is exactly the same as a stock in alphavantage we send a post-put
        key = list(response.keys())[0]
        if new_data["ticker"] == key:
            put_response = put_stocks(new_data)
            if put_response[1] == 200:
                return jsonify({"error_code": 200,"message": put_response[0]}) 
            else:
                return jsonify({"error_code": put_response[1],"message": put_response[0]}) 
        else:
            return jsonify({"error_code": 400,"message": "Ticker doesn't exists"})    
    else:
        return jsonify({"error_code": 400,"message": "Empty data"})


if __name__ == "__main__":
    app.run(debug=True)
    