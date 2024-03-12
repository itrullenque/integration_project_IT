import requests
from flask import Flask, jsonify, request, make_response, session
from flask_cors import CORS, cross_origin
import http.client
import oracledb
from models import db, Users, User_stocks
from sqlalchemy.pool import NullPool
from utilities import generate_token, hash_value

from sqlalchemy.pool import NullPool
import oracledb

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = "VFVETDZPXW4IOBLDKK"

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
        stock_ids = User_stocks.query.filter_by(user_id=user_id).with_entities(User_stocks.stock_id, 
                                                                               User_stocks.quantity, 
                                                                               User_stocks.ticker, 
                                                                               User_stocks.user_id).all()
        if stock_ids:
            return stock_ids
        else:
            return {}

    except Exception as e:
        print("Error:", str(e))

#Get the stock from oracle DB - table: USER_STOCKS
#Is a single stock_id
def get(data):

    try:
        with app.app_context():
        # Try to find an existing record
            users_response = User_stocks.query.filter_by(
                                        stock_id=data["stock_id"],
                                        user_id=data["user_id"],
                                        ).first()

        if users_response and users_response.stock_id:
            if data["stock_id"] == users_response.stock_id:
                response_dict = {
                    "stock_id": users_response.stock_id,
                    "ticker": users_response.ticker,
                    "user_id":users_response.user_id,
                    "quantity":users_response.quantity,
                    "action":data["action"]
                }
                return response_dict
            else:
                raise Exception(f"Error in the modify the stock, error_code: {users_response.status_code}")  
        else:
            raise Exception("Stock doenst found in DB")
    
    except Exception as e:
        print("Error:", str(e))
    
    return []

#Method to make a put-post request to the table USER_STOCKS
# The logic of wich action need to execute depend of the information privided by the front.
def put_stocks(data):

    #put - modify a stock that already exist in the database
    if data["action"] == "modify":
        action = "modify"
        dict_post = {
            "stock_id": data["stock_id"],
            "user_id": data["user_id"],
            "ticker": data["ticker"],
            "quantity": data["quantity"],
            "action": "modifiyed",
        }
    #post - create a new object in the database
    else:
        action = "created"
        dict_post = {
                    "stock_id": generate_token(),
                    "user_id": data["user_id"],
                    "ticker": data["ticker"].upper().strip(),
                    "quantity": int(data["quantity"]),
                    "action": "created",
                }
    
    #Preparing the data to make the request to the DB.
    if dict_post:
        if action == "created":
            try:
                new_record = User_stocks(
                                        stock_id=dict_post["stock_id"],
                                        user_id=dict_post["user_id"],
                                        ticker=dict_post["ticker"],
                                        quantity=int(dict_post["quantity"])
                                    )
                db.session.add(new_record)
                db.session.commit()
                return jsonify({"error_code": 200,"message": "Stock action successfully"})
            
            except Exception as e:
                print(f"Error: {str(e)}")

        if action == "modify":
            try:
                record_to_modify = User_stocks.query.filter_by(stock_id=dict_post["stock_id"],
                                                                user_id=dict_post["user_id"]
                                                            ).first()
                if record_to_modify:
                    record_to_modify.quantity = int(dict_post["quantity"])
                    db.session.commit()
                    return jsonify({"error_code": 200,"message": "Stock modifiyed successfully"})
                else:
                    return jsonify({"error_code": 404, "message": "Stock record not found"})   
            except Exception as e:
                print(f"Error: {str(e)}")
    else:
        return f"Failed to modify stock"

#Delete a specific stock_id from the DB
def delete_stocks(data):

    try:
        with app.app_context():
            record_delete = User_stocks.query.filter_by(
                                    stock_id=data["stock_id"],
                                    user_id=data["user_id"],
                                    ticker=data["ticker"],
                                    quantity=int(data["quantity"])
                                ).first()
            if record_delete:
                db.session.delete(record_delete)
                db.session.commit()
                return jsonify({"error_code": 200,"message": "Stock deleted successfully"})
            else:
                return jsonify({"error_code": 404, "message": "Stock record not found"})
    
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
            stock = item[2]

            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={apikey}"
            response = requests.get(url)
            data = response.json()
            stock_dict[item[2]] = {
                "stock_id":item[0],
                "quantity":item[1],
                "price": float(data["Global Quote"]["05. price"]),
                "latest_trading_day": data["Global Quote"]["07. latest trading day"],
                "total_value": round(float(data["Global Quote"]["05. price"])*item[1],2)
            }
            total_value += stock_dict[item[2]]["total_value"] #calculation of the total value of the portfolio 
        
        for stock, value in stock_dict.items():
            stock_dict[stock]["weighted_value"] = round((value["total_value"]/total_value)*100,2) #% of the representation of the stock in the portfolio

        stock_dict["portfolio_value"] = round(total_value,2)
        
        return stock_dict
    else:
        return {}

#Get the last two month by week of the relevant information of the stocks using AlphaVantage for the info.
@app.route('/ticker/<ticker>', methods=["GET"])
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
                    "quantity":int(data["newStockQuantity"]),
                    "user_id":data["userId"],
                    "action":"create"
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
                    "quantity":int(data["quantity"]),
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
        #context
        if new_data["action"] == "modify":
            action = "modifiyed"
        if new_data["action"] == "delete":
            action = "deleted"
        if new_data["action"] == "create":
            action = "created" 
        if response.status_code == 200:
            return jsonify({"error_code": 200,"message": f"Stock {action} succefully"}) 
        else:
            return jsonify({"error_code": response.default_status,"message": response.status})   
    else:
        return jsonify({"error_code": 400,"message": "Empty data"})
    
@app.route('/login', methods=["POST"])
@cross_origin()
def login():

    user_dict = request.get_json()
    user_name = False
    user_mail = False
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

        if user_name:
            users_response = Users(user_id=user_id, password=password, user_name=user_name, user_mail=user_mail)
            db.session.add(users_response)
            db.session.commit()
            return jsonify({"error_code": 200,"message": "login ok"})
        else:
            return jsonify({"error_code": 400,"message": "Error in loggin"})

if __name__ == "__main__":
    app.run(debug=True)
    