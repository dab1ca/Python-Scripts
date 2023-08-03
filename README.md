# Python-Scripts

# RedditBot collects the top thread in 5 of the user's subscribed threads and posts its title, content, top comment and the top comment contect and posts the data to a Discord server. 
# Needs the below input:
    bot_token = (f"{arguments[0]}") # Discord bot token
    client_id = (f"{arguments[1]}") # Reddit app client id
    client_secret = (f"{arguments[2]}") # Reddit app client secret
    username = (f"{arguments[3]}") # Reddit username
    password = (f"{arguments[4]}") # Reddit password

# StockBot parses a text file with indexes and check for each(from the CNN money website), whether it has risen above a certain percentage since the previous close.
# If so, it extracts information abut the stock from the Finnhub API and posts relevant data to a Discord server.
# Needs the below input

    discord_bot_token = (f"{arguments[0]}") # Discord bot token
    file_path = (f"{arguments[1]}") # Path to file containing indexes split by comma(',')
    alpha_vantage_key = (f"{arguments[2]}") # Key for Alpha Vantage API Authentication
    finnhub_api_key = (f"{arguments[3]}") # Key for Finnhub API Authentication
