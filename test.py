import requests
import json
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import http.client
import oracledb
from models import db, Users, User_stocks
from sqlalchemy.pool import NullPool
from sqlalchemy import inspect
from utilities import generate_token, hash_value

from sqlalchemy.pool import NullPool
import oracledb
from sqlalchemy import create_engine, text

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

#General variables
apikey = "VFVETDZPXW4IOBLD"

#credentials
un = 'ADMIN'
pw = 'Trullenque1990'
dsn = '(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.eu-madrid-1.oraclecloud.com))(connect_data=(service_name=g71ab6e0bc037e1_stocktrackerdb2_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'

#creating the pool
pool = oracledb.create_pool(user=un, password=pw,
                            dsn=dsn)
app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+oracledb://'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'creator': pool.acquire,
    'poolclass': NullPool
}

app.config['SQLALCHEMY_ECHO'] = True
db.init_app(app)

#Get the stock from oracle DB - table: USER_STOCKS
#Is a get all to obtain the whole data.
def get_all(user_id):

    try:
        stock_ids = User_stocks.query.filter_by(user_id=user_id).with_entities(User_stocks.stock_id).all()
        if stock_ids:
            return [stock_id for (stock_id,) in stock_ids]
        else:
            return {}

    except Exception as e:
        print("Error:", str(e))

#Get the stock from oracle DB - table: USER_STOCKS
#Is a single stock_id
def get(stock_id):

    try:
        url = f"https://g71ab6e0bc037e1-stocktrackerdb2.adb.eu-madrid-1.oraclecloudapps.com/ords/admin/user_stocks/{stock_id}" 
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if "stock_id" in data and data["stock_id"] == stock_id:
                return data
            else:
                raise Exception("Stock doenst found in DB")
        else:
            response.raise_for_status()
    
    except Exception as e:
        print("Error:", str(e))
    
    return []

#Method to make a put-post request to the table USER_STOCKS
#In the rest API of the DB, the POST and PUT works as the same, so i used the same URL to create and modify.
# The logic of wich action need to execute depend of the information privided by the front.
def put_stocks(props):

    if props["action"] != "create":
        data = get(props["stock_id"])
    #post - modify a stock that already exist in the database
    if props["action"] == "modify":
        action = "modifiyed"
        dict_post = {
            "stock_id": data["stock_id"],
            "user_id": data["user_id"],
            "ticker": data["ticker"],
            "quantity": props["quantity"],
        }
                
    #Delete method. The rest endpoint dont have a specific one to delete, so im managing add a cero in the quantity or create a new variable of state.
    elif props["action"] == "delete":
        action = "deleted"
        dict_post = {
            "stock_id": data["stock_id"],
            "portfolio_id": data["portfolio_id"],
            "user_id": data["user_id"],
            "ticker": data["ticker"],
            "quantity": data["quantity"],
        }
    #put - create a new object in the database
    else:
        action = "created"
        dict_post = {
                    "stock_id": generate_token(),
                    "user_id": props["user_id"],
                    "ticker": props["ticker"].upper().strip(),
                    "quantity": props["quantity"],
                    "action": "create",
                }
    
    #Preparing the data to make the request to the DB.
    if dict_post:
        json_data = json.dumps(dict_post)
        stock_id = dict_post["stock_id"]
        try:
            url = f"https://g71ab6e0bc037e1-stocktrackerdb2.adb.eu-madrid-1.oraclecloudapps.com/ords/admin/user_stocks/"
            response = requests.post(url,data=json_data,headers={"Content-Type": "application/json"})

            if response.status_code == 200:
                return f"Stock {action} successfully", 200
            else:
                return f"Failed to modify stock. Reason: {response.reason}", response.status_code
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        return f"Failed to modify stock"

#Delete a specific stock_id from the DB
def delete_stocks(props):

    data = get(props["stock_id"])
    stock_id = data["stock_id"]
    action = "delete"

    stock_id = data["stock_id"]
    try:
        conn = http.client.HTTPSConnection("g71ab6e0bc037e1-stocktrackerdb2.adb.eu-madrid-1.oraclecloudapps.com")
        conn.request("DELETE", f"/ords/admin/user_stocks/{stock_id}")
        response = conn.getresponse()

        if response.code == 200:
            return f"Stock {action} successfully", 200
        else:
            return f"Failed to modify stock. Reason: {response.reason}", response.status_code
    except Exception as e:
        print(f"Error: {str(e)}")

#Hompage - it render the portfolio
@app.route('/<userId>', methods=["GET"])
def homepage(userId):

    user_id = userId
    client_stocks = get_all(user_id)
    if client_stocks:
        stock_dict    = {}
        total_value = 0

        for item in client_stocks:
            stock = item["ticker"]

            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={apikey}"
            response = requests.get(url)
            data = response.json()
            stock_dict[item["ticker"]] = {
                "stock_id":item["stock_id"],
                "quantity":item["quantity"],
                "price": float(data["Global Quote"]["05. price"]),
                "latest_trading_day": data["Global Quote"]["07. latest trading day"],
                "total_value": round(float(data["Global Quote"]["05. price"])*item["quantity"],2)
            }
            total_value += stock_dict[item["ticker"]]["total_value"] #calculation of the total value of the portfolio 
        
        for stock, value in stock_dict.items():
            stock_dict[stock]["weighted_value"] = round((value["total_value"]/total_value)*100,2) #% of the representation of the stock in the portfolio

        stock_dict["portfolio_value"] = round(total_value,2)
        
        return stock_dict
    else:
        return {}

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
                return 400,"No data available for the request stock"
        else:
            raise Exception("Error obtaining the information of the stocks", "status code {}" .format(response.status_code))

    except Exception as e:
        print(str(e))

#Route to edit the portfolio.
#Create a new stock or modify a previous one in the portfolio
@app.route('/edit_stock', methods=["POST", "PUT","OPTIONS"])
@cross_origin()
def edit_portfolio():

    #Logic to manage the user request
    data = request.get_json()   
    if data and "action" in data:
        if data["action"] == "create":
            if data["newStockName"] != "":
                new_data = {
                    "action":data["action"],
                    "ticker":data["newStockName"].upper().strip(),
                    "quantity":data["newStockQuantity"],
                    "user_id":data["userId"]
                }
                response = ticker_search(new_data["ticker"]) #validate if the stock exist in alphavantage
                
                if new_data["ticker"] not in response:
                    return jsonify({"error_code": 400,"message": "No data available for the requested stock"})
            else:
                return jsonify({"error_code": 400,"message": "Empty ticker"})
        else:
            if data["selectedStock"] != "":
                new_data = {
                    "action":data["action"],
                    "ticker":data["selectedStock"],
                    "quantity":data["quantity"],
                    "stock_id":data["stockId"],
                    "user_id":data["userId"]
                }
            else:
                return jsonify({"error_code": 201,"message": "Empty ticker"})
            
        #Sending the post-put to the DB
        if new_data["action"] in ["modify", "create"]:
            response = put_stocks(new_data)
        else:
            response = delete_stocks(new_data)
        if response[1] == 200:
            return jsonify({"error_code": 200,"message": response[0]}) 
        else:
            return jsonify({"error_code": response[1],"message": response[0]})   
    else:
        return jsonify({"error_code": 400,"message": "Empty data"})
    
@app.route('/login', methods=["POST"])
@cross_origin()
def login():

    user_dict = request.get_json()
    if "userName" in user_dict:
        user_name = user_dict["userName"]
        user_mail = user_dict["userMail"]
    
    #valid for both
    user_id = user_dict["userId"]
    password = hash_value(user_dict["password"])

    with app.app_context():
    # Try to find an existing record
        users_response = Users.query.filter_by(user_id=user_id, password=password).first()

        if users_response and users_response.user_id == user_id and users_response.password == password:
            return jsonify({"error_code": 200,"message": "login ok"})

        if not users_response:
            users_response = Users(user_id=user_id, password=password, user_name=user_name, user_mail=user_mail)
            db.session.add(users_response)
            db.session.commit()
            return jsonify({"error_code": 200,"message": "login ok"})

if __name__ == "__main__":
    app.run(debug=True)
    