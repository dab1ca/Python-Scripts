import sys
import requests
import os

client_id = os.getenv('CLIENT_ID')
secret_value = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
subscriptions_list = os.getenv('SUBSCRIPTIONS') 
action_group = "<Action GROUP RESOURCE ID>"

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

subscriptions = subscriptions_list.split(',')

for subscription in subscriptions:
    activity_log_alerts_api_url = f"https://management.azure.com/subscriptions/{subscription}/providers/Microsoft.Insights/activityLogAlerts?api-version=2020-10-01"
 
    response = requests.get(activity_log_alerts_api_url, headers=headers)
    data = response.json()

    if response.status_code != 200:
        print(f"Authentication to Subscription {subscription} failed with Status Code {response.status_code}")
        continue
    
    print(f"Authentication to Subscription {subscription} successful")
    allalerts = data['value']
    
    service_health_alerts_count = 0
    for alert in allalerts:
        category = alert['properties']['condition']['allOf'][0]['equals']
        if category == 'ServiceHealth':
            service_health_alerts_count += 1
            print(f"Subscription {subscription} already has a Service Health Alert Created, skipping...")
            break
    
    if service_health_alerts_count == 0:
        alert_name = "ServiceHealth-" + f"{subscription}"
        
        resource_group_get_url = f"https://management.azure.com/subscriptions/{subscription}/resourcegroups?$top=1&api-version=2021-04-01"
        resource_group_get_response = requests.get(resource_group_get_url, headers=headers)
        rg_response = resource_group_get_response.json()
        resource_group = rg_response['value'][0]['id']
        print(resource_group)
        create_alert_rule_api_url = f"https://management.azure.com{resource_group}/providers/Microsoft.Insights/activityLogAlerts/{alert_name}?api-version=2020-10-01"
        
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
                                    },
                                    {
                                        "anyOf": [
                                            {
                                                "field": "properties.incidentType",
                                                "equals": "Incident"
                                            }
                                        ]
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
        print(f"{alert_create_request.json()}")