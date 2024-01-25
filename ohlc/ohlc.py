import pandas as pd
import json

file_path = "api_response.json"


def calculate(data):
    # Assuming your data is stored in a list of lists
    # Define column names
    columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']

    # Create a DataFrame
    df = pd.DataFrame(data, columns=columns)

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

    # Display the DataFrame with added columns
    print(df)
    csv_file_path = "output_data.csv"
    df.to_csv(csv_file_path, index=False)
    print(f"DataFrame written to {csv_file_path}")


# Read data from the file
with open(file_path, 'r') as file:
    data = json.load(file)
    calculate(data)
