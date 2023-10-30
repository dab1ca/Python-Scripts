# Python-Scripts


## Start-Stop
### Starts or deallocates virtual machines in a Subscription based on the input.
### Accepts start/deallocate as input parameters
    start-stop.py deallocate
    start-stop.py start
### Needs environment variables set
    export CLIENT_ID=<SP CLIENT ID>
    export CLIENT_SECRET=<SP CLIENT SECRET VALUE>
    export TENANT_ID=<AZURE TENANT ID>
    export SUBSCRIPTIONS=<LIST OF SUBSCRIPTIONS TO LOOP, SEPARATED BY ','>

    $Env:CLIENT_ID = <'SP CLIENT ID'>
    $Env:CLIENT_SECRET = <'SP CLIENT SECRET VALUE'>
    $Env:TENANT_ID = <'AZURE TENANT ID'>
    $Env:SUBSCRIPTIONS = <'LIST OF SUBSCRIPTIONS TO LOOP, SEPARATED BY ',''>

### Output:


![image](https://github.com/dab1ca/Python-Scripts/assets/45315505/59d31a59-4139-4970-9193-bb8da1654237)


## Create Service Health Alerts
### Loops a list of Azure Subscriptions and checks if there is a Service Health alert created in it. If not, creates an alert.
### Accepts Subscriptions as input parameters
    CreateServiceHealthAlertInput.py <SUBID_1> <SUBID_2> <SUBID_3>

### Needs environment variables set
    export CLIENT_ID=<SP CLIENT ID>
    export CLIENT_SECRET=<SP CLIENT SECRET VALUE>
    export TENANT_ID=<AZURE TENANT ID>

    $Env:CLIENT_ID = <'SP CLIENT ID'>
    $Env:CLIENT_SECRET = <'SP CLIENT SECRET VALUE'>
    $Env:TENANT_ID = <'AZURE TENANT ID'>

### Output: 

![image](https://github.com/dab1ca/Python-Scripts/assets/45315505/b18d4ae3-41bb-4ed1-a537-ff5ab935c148)


## VM Costs
### Gets a list of all VMs in a target Azure Subscription, calculates uptime in the last 30 days and estimated cost for Consumption plan, based on the VM Size. Stores vm data in a log file and prints the estimated costs for Windows/Linux/Total per Resource Group.

### Needs environment variables set
    export CLIENT_ID=<SP CLIENT ID>
    export CLIENT_SECRET=<SP CLIENT SECRET VALUE>
    export TENANT_ID=<AZURE TENANT ID>
    export SUBSCRIPTIONS=<LIST OF SUBSCRIPTIONS TO LOOP, SEPARATED BY ','>

    $Env:CLIENT_ID = <'SP CLIENT ID'>
    $Env:CLIENT_SECRET = <'SP CLIENT SECRET VALUE'>
    $Env:TENANT_ID = <'AZURE TENANT ID'>
    $Env:SUBSCRIPTIONS = <'LIST OF SUBSCRIPTIONS TO LOOP, SEPARATED BY ',''>

### Output:

![image](https://github.com/dab1ca/Python-Scripts/assets/45315505/852041a5-fc5e-4aa0-bf57-de6ff5885758)
![image](https://github.com/dab1ca/Python-Scripts/assets/45315505/e2133911-6a00-4ae8-92d5-a9ce8dce757e)


## VM Insights
### Gets a list of all VMs reporting to a target workspace and calculates: Available Time/Last Available/ Avg CPU (%)/Max CPU (%)/CPU Bottlenecks/Free Disk Space (%)/Avg RAM (GB)/Min RAM (MB)/Method of reporting
### Accepts days for report as input parameters or defaults to 7 if no input is added

### Needs environment variables set
    export CLIENT_ID=<SP CLIENT ID>
    export CLIENT_SECRET=<SP CLIENT SECRET VALUE>
    export TENANT_ID=<AZURE TENANT ID>
    export WORKSPACE_ID=<WORKSPACE ID OF THE LOG ANALYTICS WORKSPACE>

    $Env:CLIENT_ID = <'SP CLIENT ID'>
    $Env:CLIENT_SECRET = <'SP CLIENT SECRET VALUE'>
    $Env:TENANT_ID = <'AZURE TENANT ID'>
    $Env:WORKSPACE_ID = <'WORKSPACE ID OF THE LOG ANALYTICS WORKSPACE'>

### Output:

![image](https://github.com/dab1ca/Python-Scripts/assets/45315505/277808df-cd8e-4a79-a462-f909013acae3)


## Reddit bot
### RedditBot collects the top thread in 5 of the user's subscribed threads and posts its title, content, top comment and the top comment contect and posts the data to a Discord server. 
### Needs the below input:
    bot_token = (f"{arguments[0]}") # Discord bot token
    client_id = (f"{arguments[1]}") # Reddit app client id
    client_secret = (f"{arguments[2]}") # Reddit app client secret
    username = (f"{arguments[3]}") # Reddit username
    password = (f"{arguments[4]}") # Reddit password


## Stock bot
### StockBot parses a text file with indexes and check for each(from the CNN money website), whether it has risen above a certain percentage since the previous close. If so, it extracts information abut the stock from the Finnhub API and posts relevant data to a Discord server.
### Needs the below input

    discord_bot_token = (f"{arguments[0]}") # Discord bot token
    file_path = (f"{arguments[1]}") # Path to file containing indexes split by comma(',')
    alpha_vantage_key = (f"{arguments[2]}") # Key for Alpha Vantage API Authentication
    finnhub_api_key = (f"{arguments[3]}") # Key for Finnhub API Authentication
