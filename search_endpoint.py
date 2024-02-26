import requests
import json
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client_ticker = []
def portfolio():
    with open("portfolio.json") as json_file:
        data = json.load(json_file)
    
    return data

@app.route('/', methods=["GET"])
def homepage():

    client_stocks = portfolio()
    stock_dict    = {}

    for item in client_stocks["portfolios"][0]["items"]:
        stock_dict[item["ticker"]] = item["quantity"]
    
    return stock_dict

@app.route('/<ticker>', methods=["GET"])
def ticker_info(ticker):

    try:
        apikey = "VFVETDZPXW4IOBLD"
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

if __name__ == "__main__":
    app.run(debug=True)