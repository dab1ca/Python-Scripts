import requests
import sys
import os

# Define a function to process API requests and make sure that the script does not break due to throttling. If any other status code is returned by the API, the script breaks and returns the status code
def make_request(url, headers):
    request_get = requests.get(url, headers=headers)
    if request_get.status_code >= 200 and request_get.status_code <= 202:
        return request_get.json()
    elif request_get.status_code == 429:
        request_get = make_request(url, headers=headers)
        return request_get
    else:
        print(request_get.raise_for_status())
        return None

client_id = os.getenv('CLIENT_ID')
secret_value = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
subscriptions_list = os.getenv('SUBSCRIPTIONS') 

# Define input arguements, secret id and value should be passed or added as Env variables.
arguments = sys.argv[1:]
action = "" # Action should be either start or deallocate

print(arguments[0])
if len(arguments) == 0:
    print("Action preference incorrectly set. Please set action preference(arg 1) to either 'start' or 'deallocate').")
    sys.exit()
elif arguments[0] == 'deallocate' or arguments[0] == 'start':
    action = arguments[0]
else:
    print("Action preference incorrectly set. Please set action preference(arg 1) to either 'start' or 'deallocate!').")
    sys.exit()

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
    sub_counter_count += 1
    print(f"Working on Subscription {subscription} {sub_counter_count}/{sub_counter_max}")

    # Get Resource Groups from Sub
    resource_group_get_url = f"https://management.azure.com/subscriptions/{subscription}/resourcegroups?&api-version=2021-04-01"
    rg_response = make_request(resource_group_get_url, headers=headers)
    rgs = rg_response['value']

    # Resource Groups loop
    for resource_group in rgs:
        # Get all VMs in Resource Group; continue if none returned
        get_vms_rg_url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resource_group['name']}/providers/Microsoft.Compute/virtualMachines?api-version=2023-07-01"
        vms_response = make_request(get_vms_rg_url, headers=headers)
        all_vms = vms_response['value']

        if len(all_vms) == 0:
            continue

        # VM Loop
        for vm in all_vms:
            # Get VM status
            vm_status_url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resource_group['name']}/providers/Microsoft.Compute/virtualMachines/{vm['name']}/instanceView?api-version=2023-07-01"
            vm_status_response = make_request(vm_status_url, headers=headers)
            vm_status = vm_status_response['statuses'][1]['displayStatus']
            vm_current_state = ""

            if vm_status == "VM running":
                vm_current_state = "start"
            else: 
                vm_current_state = "deallocate"
            # If status doesn't match the desired state, make API request

            if vm_current_state != action:
                vm_update_url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resource_group['name']}/providers/Microsoft.Compute/virtualMachines/{vm['name']}/{action}?api-version=2023-03-01"
                vm_update_request = requests.post(vm_update_url, headers=headers)
                if action == "start":
                    print(f"Starting VM {vm['name']}")
                else:
                    print(f"Stopping VM {vm['name']}")
            else:
                print(f"Skipping VM {vm['name']}. Already in desired state: {vm_status}.")
    