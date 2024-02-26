import requests
import json


def portfolio():
    with open("portfolio.json") as json_file:
        data = json.load(json_file)
    
    return data

client_stocks = portfolio()

client_ticker =[]    
for item in client_stocks["portfolios"][0]["items"]:
    
    stock_dict = {
        item["ticker"] : item["quantity"]
    }

    client_ticker.append(stock_dict)

print(client_ticker)
