import sys
import requests
import discord
from discord.ext import commands

arguments = sys.argv[1:]

bot_token = ""
client_id = ""
client_secret = ""
username = ""
password = ""

if len(arguments) > 0:
    bot_token = (f"{arguments[0]}") # Discord bot token
    client_id = (f"{arguments[1]}") # Reddit app client id
    client_secret = (f"{arguments[2]}") # Reddit app client secret
    username = (f"{arguments[3]}") # Reddit username
    password = (f"{arguments[4]}") # Reddit password

else:
    print("No arguments provided.")
    sys.exit()

# Obtain an access token using the password grant type
auth_url = 'https://www.reddit.com/api/v1/access_token'
auth_data = {
    'grant_type': 'password',
    'username': username,
    'password': password
}

statuscode = 429

while statuscode == 429:
    auth_response = requests.post(auth_url, data=auth_data, auth=(client_id, client_secret))
    statuscode = auth_response.status_code

if auth_response.status_code == 200:
    access_token = auth_response.json()['access_token']

    # Set the headers with the access token and user agent
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Construct the API URL to list subreddits
    url = 'https://oauth.reddit.com/subreddits/mine?limit=5'

    # Send the API request
    responsecode = 429
    
    while responsecode == 429:
        response = requests.get(url, headers=headers)
        responsecode = response.status_code
    
    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        # Retrieve the JSON data from the response
        data = response.json()

        # Extract the subreddits from the JSON data
        subreddits = data['data']['children']

        # Print the name of each subreddit
        for subreddit in subreddits:
            subreddit_name = subreddit['data']['display_name']
            postmessage = ""
            print(subreddit_name)

            # Construct the API URL to get the top thread in the subreddit
            thread_url = f"https://oauth.reddit.com/r/{subreddit_name}/top.json?limit=1&t=day"

            # Send the API request to get the top thread
            threadresponsecode = 429
            while threadresponsecode == 429:
                thread_response = requests.get(thread_url, headers=headers)
                threadresponsecode = thread_response.status_code

            # Check if the request was successful (HTTP status code 200)
            if thread_response.status_code == 200:
                # Retrieve the JSON data from the response
                thread_data = thread_response.json()

                if len(thread_data['data']['children']) > 0:
                # Extract the top thread from the JSON data
                    top_thread = thread_data['data']['children'][0]['data']

                    # Extract the thread title and ID
                    thread_title = top_thread['title']
                    thread_id = top_thread['id']
                    thread_link = top_thread['permalink']

                    print(f"Top Thread: {thread_title}")
                    postmessage += (f"Top Thread: {thread_title}\n")
                    print(f"Thread Link: https://www.reddit.com{thread_link}")
                    postmessage += (f"Thread Link: https://www.reddit.com{thread_link}\n")

                    # Construct the API URL to get the top comment in the thread
                    comment_url = f"https://oauth.reddit.com/r/{subreddit_name}/comments/{thread_id}/top.json?limit=1"

                    # Send the API request to get the top comment
                    commentresponsestatuscode = 429
                    
                    while commentresponsestatuscode == 429:
                        comment_response = requests.get(comment_url, headers=headers)
                        commentresponsestatuscode = comment_response.status_code

                    # Check if the request was successful (HTTP status code 200)
                    if comment_response.status_code == 200:
                        # Retrieve the JSON data from the response
                        comment_data = comment_response.json()

                        if len(comment_data[1]['data']['children']) > 0:

                            # Extract the top comment from the JSON data
                            top_comment = comment_data[1]['data']['children'][0]['data']

                            # Extract the comment body and author
                            comment_body = top_comment['body']
                            comment_author = top_comment['author']

                            print(f"Top Comment: {comment_body}")
                            postmessage += (f"Top Comment: {comment_body}\n")
                            print(f"Comment Author: {comment_author}")
                            postmessage += (f"Comment Author: {comment_author}\n")
                        
                        else:
                            print(f"No top comment in current thread. Moving on...")
                    else:
                        print(f"No top comment in current thread. Moving on...")
                    
                    # Set up the bot command prefix
                    bot = commands.Bot(intents=discord.Intents.default(),command_prefix='!')

                    @bot.event
                    async def on_ready():
                        print(f'Logged in as {bot.user.name} ({bot.user.id})')

                        # Post a message on your behalf
                        channel = bot.get_channel(1129763555911147634)  # Replace with the desired channel ID
                        await channel.send(f"{postmessage}")

                        # Disconnect the bot from Discord
                        await bot.close()
                    
                    bot.run(bot_token)

                else:
                    print(f"No top thread in subreddit {subreddit_name} for the last 24h. Moving on...")

            else:
                print(f"Failed to retrieve top thread for subreddit {subreddit_name}. Request failed with status code {thread_response.status_code}.")
                continue

                print("------")
    else:
        print(f'Request failed with status code {response.status_code}.')
else:
    print(f'Authentication failed with status code {auth_response.status_code}.')

