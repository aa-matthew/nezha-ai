import requests

url = "https://api.geckoterminal.com/api/v2/networks/eth/pools/0x60594a405d53811d3bc4766596efd80fd545a270/ohlcv/hour?limit=1000"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    data = data.get("data").get("attributes").get("ohlcv_list")

    file_path = "api_response.json"

    # Write the data to a file
    with open(file_path, 'w') as file:
        file.write(str(data))

    # Process the response data as needed
    print(data)
else:
    print(f"Error: {response.status_code}, {response.text}")
