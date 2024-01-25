import re
import requests
import google.generativeai as genai
import time
from prompts_library import *

import pandas as pd
from datetime import datetime
import os
# from dotenv import load_dotenv
# load_dotenv()
MAPPING_TOKEN = {
    "pepe": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
    "oraichain": "0xA325Ad6D9c92B55A3Fc5aD7e412B1518F96441C0"
}

PROJECTS = ["pepe", "oraichain", "floky"]


# genai_key = os.environ["GENAI_KEY"]
genai_key = "AIzaSyCDnOKby9z9fdfGdUs9sQgbZk7rfJCLWXE"
genai.configure(api_key=genai_key)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

model = genai.GenerativeModel('gemini-pro')


def get_ohlcv_data(network, pool_address, timeframe):
    base_url = 'https://api.geckoterminal.com/api/v2/networks'
    endpoint = f'{network}/pools/{pool_address}/ohlcv/{timeframe }'
    url = f'{base_url}/{endpoint}'
    headers = {'accept': 'application/json'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # If the request was successful, return the JSON response
        return response.json()['data']['attributes']['ohlcv_list']

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def get_ohlc_data_from_guru(network, address, time_frame):
    symbol = f"{address}-{network}_USD"
    url = f"https://api.dev.dex.guru/v1/tradingview/history?symbol={symbol}&resolution=1D&from=1700017600&currencyCode=USD"

    payload = {}
    headers = {
        'accept': 'application/json',
        'api-key': 'gro_NP8URC3OW9BF0lDpM0YJRSzFbPT5V0ujxZtsJ0U'
    }
    try:

        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # If the request was successful, return the JSON response
        data = response.json()
        res = []
        for i in range(len(data["t"])):
            res.append([
                data["t"][i],
                data["o"][i],
                data["h"][i],
                data["l"][i],
                data["c"][i],
                data["v"][i],
            ])
        print("DATA length", len(res))

        return res

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def process_ohlcv_data(ohlcv_list, pool_address):

    # Convert the list of lists to a DataFrame
    df = pd.DataFrame(ohlcv_list, columns=[
        'Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])

    # Convert the Timestamp column to datetime format
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')

    # Calculate SMA 50
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # Calculate EMA 20
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

    # Calculate MACD
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Calculate Bollinger Bands
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Std_Dev'] = df['Close'].rolling(window=20).std()
    df['Bollinger_Upper'] = df['SMA_20'] + 2 * df['Std_Dev']
    df['Bollinger_Lower'] = df['SMA_20'] - 2 * df['Std_Dev']

    most_recent_values = {
        'EMA_50': df['SMA_50'].iloc[-1],
        'SMA_20': df['SMA_20'].iloc[-1],
        'EMA_20': df['EMA_20'].iloc[-1],
        'MACD': df['MACD'].iloc[-1],
        'Signal_Line': df['Signal_Line'].iloc[-1],
        'Bollinger_Upper': df['Bollinger_Upper'].iloc[-1],
        'Bollinger_Lower': df['Bollinger_Lower'].iloc[-1]
    }
    for i in most_recent_values.keys():
        most_recent_values[i] = round(most_recent_values[i], 5)
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    most_recent_values["Date"] = formatted_datetime
    most_recent_values["Analyst"] = "Pearl AI"
    most_recent_values["Pool_address"] = pool_address
    return most_recent_values


def get_gemini_response(inputs=""):
    response = model.generate_content(
        inputs,
        safety_settings={
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
            'HARM_CATEGORY_HATE_SPEECH': 'block_none',
            'HARM_CATEGORY_HARASSMENT': 'block_none',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none'
        },
        # stream = False
    )
    return response


def get_ta(stats):
    inputs = ANALYZE_PROMPT.replace("$$STATS$$", str(stats))
    print("TA input: \n", inputs)
    response = get_gemini_response(inputs)

    return response.text


# with open("./data/pepe.txt", encoding = "utf8") as f:
#     data = f.readlines()
# queries = "".join(data).split("\n\n")


def extract_user_and_query(text):
    # Define a regular expression pattern to match the user and query
    pattern = r'> (\w+):\n(.*)'

    # Use re.match to find the first occurrence of the pattern in the text
    match = re.match(pattern, text)

    if match:
        # Extract the user and query from the matched groups
        user = match.group(1)
        query = match.group(2)
        return {'user': user, 'query': query}
    else:
        # Return None if no match is found
        return None


def get_sentiment(queries):
    prompt = SENTIMENT_PROMPT_TEMPLATE.replace("$$QUERY$$", queries)
    response = model.generate_content(
        prompt,
        safety_settings={
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
            'HARM_CATEGORY_HATE_SPEECH': 'block_none',
            'HARM_CATEGORY_HARASSMENT': 'block_none',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none'
        }
    )
    try:
        # print(response.text)
        return eval(response.text.replace("```json", "").replace("```", ""))
    except:
        print(response.prompt_feedback)
        # return None
        return ""


def format_json_to_report(json_data):
    report = "Observations from the queries:\n" + \
        json_data['Observations from the queries'] + "\n\n"
    report += "Overall Sentiment: " + json_data['Overall Sentiment'] + "\n\n"

    for detail in json_data['detail']:
        report += f"Detail: {detail['detailed observation']}\n"
        report += f"Sentiment: {detail['sentiment']}\n\n"

    return report


def format_history(history, message):
    messages = [
        {
            'role': 'user',
            'parts': [SYSTEM_PROMPT]
        },
        {
            'role': "model",
            "parts": ["Understood."]
        }
    ]
    for i in history:
        messages.append({
            "role": "user",
            "parts": [i[0]]
        })
        messages.append({
            "role": "model",
            "parts": [i[1]]
        })
    messages.append({
        "role": "user",
        "parts": [message]
    })
    return messages


def simple_qa(message, history):
    inputs = format_history(history, message)
    response = get_gemini_response(inputs)
    return response.text


def get_address(query):
    prompt = MAPPING_TOKEN.replace("$$QUERY$$", query)
    response = model.generate_content(
        prompt,
        safety_settings={
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
            'HARM_CATEGORY_HATE_SPEECH': 'block_none',
            'HARM_CATEGORY_HARASSMENT': 'block_none',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none'
        }
    )
    try:
        # print(response.text)
        return response.text
    except:
        print(response.prompt_feedback)
        # return None
        return ""


def controller(query, history):
    try:
        print(query)
        inputs = CONTROLLER_PROMPT_TEMPLATE.replace("$$QUERY$$", query)
        print("Controller input: \n", inputs)
        planner_response = get_gemini_response(inputs)
        plan = eval(planner_response.text.replace(
            "```json", "").replace("```", ""))
        answer = ""
        print("the plan:", plan)
        time.sleep(2)
        if plan["action"] == "Technical analyze":
            try:
                network = plan["params"]["network"]
            except:
                network = "eth"
            try:
                pool_address = plan["params"]["pool_address"]
            except:
                return "Please tell me the pool address."
            try:
                timeframe = plan["params"]["timeframe"]
            except:
                timeframe = "day"
            ohlcv_data = get_ohlc_data_from_guru(
                network, pool_address, timeframe)
            processed_data = process_ohlcv_data(ohlcv_data, pool_address)
            print(processed_data)
            response = get_ta(processed_data)
            # for i in get_ta(processed_data):
            #     yield i
        elif plan["action"] == "Sentiment analyze":
            print("yah")
            try:
                token_name = plan["params"]["token_name"]
            except:
                return f"Error, please try later"
            if token_name.lower() in PROJECTS:
                with open(f"./data/{token_name}.txt", encoding="utf8") as f:
                    data = f.readlines()
                queries = "".join(data).split("\n\n>")
                formatted_queries = [
                    extract_user_and_query(">"+i) for i in queries]
                print("working")
                response = format_json_to_report(
                    get_sentiment(str(formatted_queries)))
                print(response)
            else:
                return f"Not supported Sentiment analysis for {token_name} yet"
        elif plan["action"] == "On-chain question answering":
            response = get_address(query)
        elif plan["action"] == 'Project question answering':
            response = get_address(query)
        else:
            response = simple_qa(query, history)
            # for i in simple_qa(query, history):
            #     yield i
        # print(response)

        return response

    except:
        return "Error, please try later"


# controller("tell me stats of 0x9081b50bad8beefac48cc616694c26b027c559bb on eth", [])
# controller("hello", [])
# print(controller("how this pool going on eth, pool address 0xe4b8583ccb95b25737c016ac88e539d0605949e8",[]))
print(controller("give me sentiment of the community about floky", []))
