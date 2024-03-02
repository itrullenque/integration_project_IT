import requests
import json
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

apikey = "VFVETDZPXW4IOBLD"

client_ticker = []
def portfolio():
    with open("portfolio.json") as json_file:
        data = json.load(json_file)
    
    return data

@app.route('/', methods=["GET"])
def homepage():

    client_stocks = portfolio()
    stock_dict    = {}
    total_value = 0

    for item in client_stocks["portfolios"][0]["items"]:
        stock = item["ticker"]

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
        total_value += stock_dict[item["ticker"]]["total_value"]
        
    for stock, value in stock_dict.items():
        stock_dict[stock]["weighted_value"] = round((value["total_value"]/total_value)*100,2)

    stock_dict["portfolio_value"] = total_value
    
    return stock_dict

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


if __name__ == "__main__":
    app.run(debug=True)