import requests
import json


try:
    apikey = "VFVETDZPXW4IOBLD"
    stock = "AAPL"
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={stock}&apikey={apikey}"
    
    response = requests.get(url)
    value = response.raise_for_status()
    if response.status_code == 200:
        data = response.json()
        if data["bestMatches"] != []:
            stock_dict = {}
            for stock in data["bestMatches"]:
                stock_dict[stock["1. symbol"]] = stock["2. name"]
            
            stock_dict
        else:
            "No data available for the request stock"
    else:
        raise Exception("Error obtaining the information of the stocks", "status code {}" .format(response.status_code))

except Exception as e:
    print(str(e))
