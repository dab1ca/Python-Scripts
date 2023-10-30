import requests
import os
import sys

arguments = sys.argv[1:]
subscriptions = []

if len(arguments) == 0:
    print("Subscription not added")
    sys.exit()
else:
    for sub in arguments:
        subscriptions.append(sub)

client_id = os.getenv('CLIENT_ID')
secret_value = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
action_group = "<ADD ACTION GROUP RESOURCE ID>"

auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': secret_value,
            'scope': 'https://management.azure.com/.default'
}
 
auth_response = requests.post(auth_url, data=auth_data)
access_token = auth_response.json()['access_token']

headers = {
            'Authorization': f'Bearer {access_token}'
}

for subscription in subscriptions:
    subscription_get_api_url = f"https://management.azure.com/subscriptions/{subscription}?api-version=2022-12-01"
    sub_get_response = requests.get(subscription_get_api_url, headers=headers)

    if sub_get_response.status_code != 200:
        print(f"Authentication to Subscription {subscription} failed with Status Code {sub_get_response.status_code}")
        continue

    sub_info = sub_get_response.json()
    subscription_name = sub_info['displayName']

    activity_log_alerts_api_url = f"https://management.azure.com/subscriptions/{subscription}/providers/Microsoft.Insights/activityLogAlerts?api-version=2020-10-01"
 
    activity_log_alerts_api_response = requests.get(activity_log_alerts_api_url, headers=headers)
    alerts_data = activity_log_alerts_api_response.json()
    
    print(f"Authentication to Subscription {subscription_name} successful")
    allalerts = alerts_data['value']
    
    service_health_alerts_count = 0
    for alert in allalerts:
        category = alert['properties']['condition']['allOf'][0]['equals']
        if category == 'ServiceHealth':
            service_health_alerts_count += 1
            print(f"Subscription {subscription_name} already has a Service Health Alert Created, skipping...")
            break
    
    if service_health_alerts_count == 0:
        alert_name = f"{subscription_name} - " + "ServiceHealth"
        
        resource_group_get_url = f"https://management.azure.com/subscriptions/{subscription}/resourcegroups?$top=1&api-version=2021-04-01"
        resource_group_get_response = requests.get(resource_group_get_url, headers=headers)
        rg_response = resource_group_get_response.json()
        resource_group = "ServiceHealthRG"
        if len(rg_response['value']) > 0:
            resource_group_id = rg_response['value'][0]['id']
            resource_group = resource_group_id.split('/')[4]
        else: 
            resource_group_create_url = f"https://management.azure.com/subscriptions/{subscription}/resourcegroups/{resource_group}?api-version=2021-04-01"
            rg_body = {
                        "location": "westus"
            }
            requests.put(resource_group_create_url, json = rg_body, headers=headers)

        create_alert_rule_api_url = f"https://management.azure.com/subscriptions/{subscription}/resourcegroups/{resource_group}/providers/Microsoft.Insights/activityLogAlerts/{alert_name}?api-version=2020-10-01"
        
        alert_body = {
                        "location": "Global",
                        "tags": {},
                        "properties": {
                            "scopes": [
                                f"/subscriptions/{subscription}"
                            ],
                            "condition": {
                                "allOf": [
                                    {
                                        "field": "category",
                                        "equals": "ServiceHealth"
                                    }
                                ]
                            },
                            "actions": {
                                "actionGroups": [
                                    {
                                        "actionGroupId": f"{action_group}",
                                        "webhookProperties": {}
                                    }
                                ]
                            },
                            "enabled": "true",
                            "description": "Created with API"
                        }
        }
        
        alert_create_request = requests.put(create_alert_rule_api_url, json = alert_body, headers=headers)
        alert_create_response_json = alert_create_request.json()
        alert_name = alert_create_response_json['name']
        print(f"Alert {alert_name} was created successfully in Subscrtipion {subscription_name}")
