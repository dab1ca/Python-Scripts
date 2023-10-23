import requests
from datetime import datetime, timedelta
from tabulate import tabulate
import os
from pathlib import Path
import time
import progressbar

# ------------------------------ FUNCTIONS ----------------------------
# Define a function to process API requests and make sure that the script does not break due to throttling. If any other status code is returned by the API, the script breaks and returns the status code
def make_request(url, headers):
    request_get = requests.get(url, headers=headers)
    if request_get.status_code == 200:
        return request_get.json()
    elif request_get.status_code == 429:
        request_get = make_request(url, headers=headers)
        return request_get
    else:
        print(request_get.status_code)
        return None

# Define functions to get current user and OS for logfile creation. Logs will be stored in C:\Users\<USER>\log for Windows and /home/<USER>/log for Linux
def get_current_user():
    current_user = os.getenv('USER')
    return current_user

def get_os():
    if os.name == 'posix':
        return "Linux"
    else:
        return "Windows"

# Define function to create directory, based on the OS
def check_and_create_logs_directory_and_file(ostype, user, current_date):
    if ostype == "Windows":
        path = rf"C:\Users\{user}\log"
        # Check if directory exists and create directory if not
        if not os.path.exists(path):
            os.mkdir(path)
        
        # Create  empty log file
        file_path = Path(rf'C:\Users\{user}\log\vms-{current_date}.log')
        file_path.touch()
        return file_path
    else:
        path = f'/home/{user}/log'
        # Check if directory exists and create directory if not
        if not os.path.exists(path):
            os.mkdir(path)
        
        # Create  empty log file
        file_path = Path(f"/home/{user}/log/vms-{current_date}.log")
        file_path.touch()
        return file_path


# ------------------------------ MAIN LOGIC ----------------------------

client_id = os.getenv('CLIENT_ID')
secret_value = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
subscriptions_list = os.getenv('SUBSCRIPTIONS') 

# Get current date and query start date(30 days ago) and format it for the API query
current_date = datetime.now()
query_end_period = current_date.strftime('%Y-%m-%dT%H:%M:%S')
start_date = current_date - timedelta(days=30)
query_start_period = start_date.strftime('%Y-%m-%dT%H:%M:%S')

# Create the log file
current_user = get_current_user()
current_os = get_os()
log_file = Path(check_and_create_logs_directory_and_file(current_os, current_user, query_end_period))

# Get access token and define the authentication header for requests. Scope might need to be changed depending on the actions
auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id, # Should be defined with input parameters/Env variables
            'client_secret': secret_value, # Should be defined with input parameters/Env variables
            'scope': 'https://management.azure.com/.default'
}
 
auth_response = requests.post(auth_url, data=auth_data)
access_token = auth_response.json()['access_token']
 
headers = {
            'Authorization': f'Bearer {access_token}'
}

# Define subscriptions list
subscriptions = subscriptions_list.split(',')
sub_counter_count = 0
sub_counter_max = len(subscriptions)

# Subscriptions loop
for subscription in subscriptions:
    # Print job status
    sub_counter_count += 1
    print(f"Working on Subscription {subscription} {sub_counter_count}/{sub_counter_max}")
    
    # Get Resource Groups from Sub
    resource_group_get_url = f"https://management.azure.com/subscriptions/{subscription}/resourcegroups?&api-version=2021-04-01"
    rg_response = make_request(resource_group_get_url, headers=headers)
    rgs = rg_response['value']

    # Define the output table for costs per resource group/OS
    table_data_rgs = []
    table_data_rgs.append(['Name', 'OSType', 'Cost'])

    # Progress bar for current Subscription
    widgets = [' [',
         progressbar.Timer(format= 'elapsed time: %(elapsed)s'),
         '] ',
           progressbar.Bar('*'),' (',
           progressbar.ETA(), ') ',
          ]
 
    bar = progressbar.ProgressBar(max_value=len(rgs), widgets=widgets).start()
    bar_count = 0

    # Resource Groups loop
    for resource_group in rgs:
        
        # Get all VMs in RG
        get_vms_rg_url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resource_group['name']}/providers/Microsoft.Compute/virtualMachines?api-version=2023-07-01"
        vms_response = make_request(get_vms_rg_url, headers=headers)
        all_vms = vms_response['value']

        # Silently continue if no VMs created in RG
        if len(all_vms) == 0:
            continue
        
        linux_vms = []
        windows_vms = []
        # VMs Loop
        for vm in all_vms:
            # Define the VM Print dict(for log data)
            vm_print = {}
            vm_print['name'] = vm['name']
            vm_print['vm_series'] = vm['properties']['hardwareProfile']['vmSize']
            vm_print['os_name'] = vm['properties']['storageProfile']['osDisk']['osType']
            vm_print['os_publisher'] = vm['properties']['storageProfile']['imageReference']['publisher']
            vm_print['os_sku'] = vm['properties']['storageProfile']['imageReference']['sku']
            vm_print['location'] = vm['location']
            
            # Get the VM Availability metric to calculate used time and the Percentage CPU to calculate load.
            metric_url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resource_group['name']}/providers/Microsoft.Compute/virtualMachines/{vm_print['name']}/providers/Microsoft.Insights/metrics?interval=PT24H&metricnames=VmAvailabilityMetric,Percentage CPU&aggregation=count&api-version=2018-01-01&metricnamespace=microsoft.compute/virtualmachines&timespan={query_start_period}/{query_end_period}"
            metric_response = make_request(metric_url, headers=headers)

            # Calculate the total VM Availability in minutes
            availability_metric_values = metric_response['value'][0]['timeseries']      
            total_usage_minutes = 0
            if len(availability_metric_values) > 0:
                for tick in availability_metric_values[0]['data']:
                    if 'count' in tick:
                        total_usage_minutes += tick['count']
            
            vm_print['total_usage_minutes'] = total_usage_minutes

            # Calculate the average cpu usage for the respective period(periods with no data are excluded from the calculation). Maximum metric granularity is 24h
            cpu_usage_metric_values = metric_response['value'][1]['timeseries']
            cpu_usage = 0
            count = 0

            if len(cpu_usage_metric_values) > 0:
                for tick in cpu_usage_metric_values[0]['data']:
                    if 'average' in tick:
                        cpu_usage += tick['average']
                        count += 1
            
            vm_print['average_cpu_usage'] = 0
            if count > 0:
                vm_print['average_cpu_usage'] = cpu_usage/count


            # Get the costs for Consumption plan for the respective VM series.
            cost_url = f"https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armSkuName eq '{vm_print['vm_series']}' and armRegionName eq '{vm_print['location']}' and type eq 'Consumption' and isPrimaryMeterRegion eq true"   
            vm_cost_response = make_request(cost_url, headers=headers)
            vm_print['vm_price_per_hour'] = 0

            for plan in vm_cost_response['Items']:
                if vm_print['os_name'] == "Windows" and 'licenseType' in vm['properties']: 
                    if "Windows" in plan['productName']:
                        vm_print['vm_price_per_hour'] = plan['unitPrice']
                else:
                    if plan['productName'].find("Windows") == -1:
                        vm_print['vm_price_per_hour'] = plan['unitPrice']
            if vm_print['os_name'] == "Linux":
                linux_vms.append(vm_print)
            elif vm_print['os_name'] == "Windows":
                windows_vms.append(vm_print)
            else:
                print(f"Error getting OS information for VM {vm_print['name']}. Got {vm_print['os_name']}")

        # Calculate the total cost for Linux VMs in the Resource Group(script output) and log the collected information for VMs(log file)
        total_cost_for_rg_linux = 0
        for linux_vm in linux_vms:
            usage_hours = linux_vm['total_usage_minutes'] // 60
            total_cost = usage_hours*linux_vm['vm_price_per_hour']
            
            with open(log_file, 'a') as file:
                log_data = f"{query_end_period}/{linux_vm['name']}/{linux_vm['os_name']}/{linux_vm['os_publisher']}/{linux_vm['os_sku']}/{linux_vm['location']}/{linux_vm['vm_series']}/{linux_vm['average_cpu_usage']}/{linux_vm['total_usage_minutes']}/{linux_vm['vm_price_per_hour']}/{total_cost}"
                file.write(log_data + '\n')
            
            total_cost_for_rg_linux += total_cost
        
        table_data_rgs.append([resource_group['name'], 'Linux', total_cost_for_rg_linux])

        # Calculate the total cost for Windows VMs in the Resource Group(script output) and log the collected information for VMs(log file)
        total_cost_for_rg_windows = 0
        for windows_vm in windows_vms:
            usage_hours = windows_vm['total_usage_minutes'] // 60
            total_cost = usage_hours*windows_vm['vm_price_per_hour']
           
            with open(log_file, 'a') as file:
                log_data = f"{query_end_period}/{windows_vm['name']}/{windows_vm['os_name']}/{windows_vm['os_publisher']}/{windows_vm['os_sku']}/{windows_vm['location']}/{windows_vm['vm_series']}/{windows_vm['average_cpu_usage']}/{usage_hours}/{windows_vm['vm_price_per_hour']}/{total_cost}"
                file.write(log_data + '\n')
            total_cost_for_rg_windows += total_cost

        table_data_rgs.append([resource_group['name'], 'Windows', total_cost_for_rg_windows])
        
        # Calculate total cost for RG
        sum = total_cost_for_rg_windows + total_cost_for_rg_linux
        table_data_rgs.append([resource_group['name'], 'Total', sum])
        
        bar_count += 1
        bar.update(bar_count)
    print(tabulate(table_data_rgs, headers='firstrow', tablefmt='psql', floatfmt=".2f"))

    


    
            








