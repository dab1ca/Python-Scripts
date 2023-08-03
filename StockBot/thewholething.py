from bs4 import BeautifulSoup
import requests
import re
import finnhub
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import sys

# ======================================== 1. Variables ========================================
discord_bot_token = ""
file_path = ""
alpha_vantage_key = ""
finnhub_api_key = ""

arguments = sys.argv[1:]

if len(arguments) > 0:
    discord_bot_token = (f"{arguments[0]}") # Discord bot token
    file_path = (f"{arguments[1]}") # Path to file containing indexes split by comma(',')
    alpha_vantage_key = (f"{arguments[2]}") # Key for Alpha Vantage API Authentication
    finnhub_api_key = (f"{arguments[3]}") # Key for Finnhub API Authentication

# Define finnhub auth
finnhub_client = finnhub.Client(api_key=(f"{finnhub_api_key}"))

# ======================================== 2. Functions ========================================
# Define the function to extract Company data from alhavantage API
def get_alpha_vantage_company_info(company):
    response = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={company}&apikey={alpha_vantage_key}")

    if response.status_code != 200:
        return None
    
    else:
        return response.json()

# Define the function to extract the date of the last refresh from the CNN Website
def convert_date_string_cnn_web(input_string):
    # Get current year
    current_year = datetime.now().year
    # Extract date
    date_string = input_string.split(' ')[-1]
    month_string = input_string.split(' ')[-2]
    # Add current year
    full_date_string = f"{month_string} {date_string} {current_year}"

    # Convert to datetime object
    date_object = datetime.strptime(full_date_string, '%b %d %Y')

    return date_object

# Define the function to extract Stock data from provided URL
def extract_data_from_url(url):
    extracted_data = {}
    extracted_data['Stock URL'] = (f"https://money.cnn.com/quote/quote.html?symb={url}")
    response = requests.get(f"{extracted_data['Stock URL']}")
    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extracting the first cell
    extracted_data['Last Price'] = "N/A"
    first_cell = soup.find('td', class_='wsod_last')

    if first_cell != None:
        extracted_data['Last Price'] = first_cell.find('span', stream=re.compile(r"last_\d+")).text.strip()
        
    # Extracting the second cell
    extracted_data['Change Total'] = "N/A"
    second_cell = soup.find('td', class_='wsod_change')

    if second_cell != None:
        change_total = second_cell.find('span', stream=re.compile(r"change_\d+"))
       
        if (change_total.find('span', class_="posData")) == None:
            return None
        
        else:
            extracted_data['Change Total'] = change_total.find('span', class_="posData").text.strip()

        change_percent = second_cell.find('span', stream=re.compile(r"changePct_\d+"))
        
        if (change_percent.find('span', class_="posData")) == None:
            return None
        
        else:
            extracted_data['Change Percent'] = float((change_percent.find('span', class_="posData").text.strip()).rstrip('%'))


    try:
        fourth_cell = soup.find('div', class_='wsod_quoteLabelAsOf').text.strip()
        extracted_data['LastRefresh'] = convert_date_string_cnn_web(fourth_cell)
        extracted_data['DataAge'] = datetime.now() - extracted_data['LastRefresh']

    except Exception as e:
        return None

    return extracted_data


# ======================================== 3. Main ========================================
# Open the file in read mode
with open(file_path, 'r') as file:
    # Read the entire content of the file
    content = file.read()

# Split the content
stocks_to_check = content.split(',')

for stock in stocks_to_check:
# ======================================== 3.1 Data Scraping ========================================    
    extracted_data_for_stock_cnn = extract_data_from_url(stock)

    #if the data is stale, skip to the next iteration
    if (extracted_data_for_stock_cnn == None) or (extracted_data_for_stock_cnn['DataAge'] > timedelta(days=4)):
        continue
    
    daily_rise = extracted_data_for_stock_cnn['Change Percent']
    current_price_cnn = extracted_data_for_stock_cnn['Last Price']
    
    #if the rise in percent is less than the defined, skip to the next iteration
    if (daily_rise < 2):
        continue

    #Get stock profile from Aplha Vantage
    alpha_vantage_stock_profile = get_alpha_vantage_company_info(stock)
    
    #Define variables from Alpha Vantage stock quote
    stock_company_name = alpha_vantage_stock_profile['Name']
    stock_company_sector = alpha_vantage_stock_profile['Sector']
    high_52 = alpha_vantage_stock_profile['52WeekHigh']
    low_52 = alpha_vantage_stock_profile['52WeekLow']
    ma_50 = alpha_vantage_stock_profile['50DayMovingAverage']
    ma_200 = alpha_vantage_stock_profile['200DayMovingAverage']
    quarterly_earnings_yoy = alpha_vantage_stock_profile['QuarterlyEarningsGrowthYOY']
    quarterly_revenue_yoy = alpha_vantage_stock_profile['QuarterlyRevenueGrowthYOY']
    price_target = alpha_vantage_stock_profile['AnalystTargetPrice']

    # Get news about the stock from Finnhub
    finnhub_stock_news = finnhub_client.company_news((f"{stock}"), _from=(f"{(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}"), to=(f"{(datetime.now()).strftime('%Y-%m-%d')}"))
    
    # Get quote about the stock from Finnhub
    finnhub_quote = finnhub_client.quote((f"{stock}"))
    
    # Define variables from Finnhub stock quote 
    current_price_finnhub = finnhub_quote['c']
    yesterday_close_finnhub = finnhub_quote['pc']
    open_price_finnhub = finnhub_quote['o']
    percent_change_finnhub = finnhub_quote['dp']


# ======================================== 3.2 Data Distribution ======================================== 
    # Set up the bot command prefix
    bot = commands.Bot(intents=discord.Intents.default(),command_prefix='!')

    @bot.event
    async def on_ready():
        # Post a message on your behalf
        channel = bot.get_channel(1129763555911147634)  # Replace with the desired channel ID
        await channel.send(f"Stock {stock} has risen with {daily_rise}% today(According to CNN website data - Finnhub price has risen {percent_change_finnhub}%).\nHere are some details about the stock:\nFull Company Name: {stock_company_name}\nSector: {stock_company_sector}\nCurrent Price(CNN): {current_price_cnn}\nCurrent Price(Finnhub): {current_price_finnhub}\nYesterday Close: {yesterday_close_finnhub}\nToday's open: {open_price_finnhub}")
        await channel.send(f"Here is also some historical data about the stock:\n52-week high: {high_52}\n52-week low: {low_52}\nMA 50: {ma_50}\nMA 200: {ma_200}\nQuarterly Earnings Growth YOY: {quarterly_earnings_yoy}\nQuarterly Revenue Growth YOY: {quarterly_revenue_yoy}\nAnalyst price target: {price_target}")
        await channel.send(f"And also some news about the company:")

        for news in finnhub_stock_news:

            # Parse the news information
            news_timestamp = (datetime.utcfromtimestamp(news['datetime'])).strftime("%Y-%m-%d %H:%M:%S")
            news_title = news['headline']
            news_url = news['url']
            news_source = news['source']

            await channel.send(f"Source: {news_source}\nTime of posting: {news_timestamp}\nUrl: {news_url}\n{news_title}")
      
        # Disconnect the bot from Discord
        await bot.close()
                    
    bot.run(discord_bot_token)
