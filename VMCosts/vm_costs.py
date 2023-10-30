import os
import requests
import math
from tabulate import tabulate
from datetime import datetime
import progressbar
import sys

arguments = sys.argv[1:]
query_period = 7
if len(arguments) != 0:
    query_period = arguments[0]

query_period = 7

client_id = os.getenv('CLIENT_ID')
secret_value = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
workspace_id = os.getenv('WORKSPACE_ID')

# Get access token and define the authentication header for requests. Scope might need to be changed depending on the actions
auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id, # Should be defined with input parameters/Env variables
            'client_secret': secret_value, # Should be defined with input parameters/Env variables
            'resource': 'https://api.loganalytics.io'
}

auth_response = requests.post(auth_url, data=auth_data)
access_token = auth_response.json()['access_token']
 
headers = {
            'Authorization': f'Bearer {access_token}'
}

# Get the list of machines reporting to the target workspace
log_analytics_query_url = f"https://api.loganalytics.azure.com/v1/workspaces/{workspace_id}/query"

post_body = {
   	"query": f"let metrictimespan = ago({query_period}d); Heartbeat \
                | where TimeGenerated > metrictimespan \
                | summarize hbcount = count(), lastHeartBeat = max(TimeGenerated) by Computer, OSType \
                | join kind=leftouter (InsightsMetrics \
                | where TimeGenerated > metrictimespan and Name == 'UtilizationPercentage' \
                | summarize AvgCPUUsageInsights = avg(Val), MaxCPUUsageInsights = max(Val) by Computer) on Computer, $left.Computer == $right.Computer \
                | join kind=leftouter (InsightsMetrics \
                | where TimeGenerated > metrictimespan and Name == 'FreeSpacePercentage' \
                | extend Disk=tostring(todynamic(Tags)['vm.azm.ms/mountId']) \
                | where Disk == 'C:' or Disk == '/' \
                | summarize FreeDiskSpaceInsights = avg(Val) by Computer) on Computer, $left.Computer == $right.Computer \
                | join kind=leftouter (InsightsMetrics \
                | where TimeGenerated > metrictimespan and Name == 'AvailableMB' \
                | summarize AvgAvailableRAMinGBInsights = avg(Val)/1000, MinAvailableRAMinMBInsights = min(Val) by Computer) on Computer, $left.Computer == $right.Computer \
                | join kind=leftouter (Perf \
                | where TimeGenerated > metrictimespan and CounterName == '% Processor Time' \
                | summarize AvgCPUUsagePerf = avg(CounterValue), MaxCPUUsagePerf = max(CounterValue) by Computer) on Computer, $left.Computer == $right.Computer \
                | join kind=leftouter (Perf \
                | where TimeGenerated > metrictimespan \
                | where CounterName == 'Available MBytes Memory' or CounterName == 'Available MBytes' or CounterName == 'Available Bytes' \
                | extend AvailableMbytes = case(CounterName == 'Available Bytes', CounterValue/1048576, CounterValue) \
                | summarize AvgMemoryUsageGBPerf = avg(AvailableMbytes)/1000, MinMemoryUsageMBPerf = min(AvailableMbytes) by Computer) on Computer, $left.Computer == $right.Computer \
                | join kind=leftouter (Perf \
                | where TimeGenerated > metrictimespan and CounterName == '% Free Space' \
                | where InstanceName == 'C:' or InstanceName == '/' \
                | summarize FreeDiskSpacePerf = avg(CounterValue) by Computer) on Computer, $left.Computer == $right.Computer \
                | extend reportingMethod = case(isnull(AvgCPUUsageInsights), 'Perf', 'Insights') \
                | project Computer, OSType, hbcount, lastHeartBeat, \
                AvgCPUUsage = case(reportingMethod == 'Insights', AvgCPUUsageInsights, AvgCPUUsagePerf), \
                MaxCPUUsage = case(reportingMethod == 'Insights', MaxCPUUsageInsights, MaxCPUUsagePerf), \
                FreeDiskSpace = case(reportingMethod == 'Insights', FreeDiskSpaceInsights, FreeDiskSpacePerf), \
                AvgAvailableRAMinGB = case(reportingMethod == 'Insights', AvgAvailableRAMinGBInsights, AvgMemoryUsageGBPerf), \
                MinAvailableRAMinMB = case(reportingMethod == 'Insights', MinAvailableRAMinMBInsights, MinMemoryUsageMBPerf), \
                reportingMethod" 
}

general_query_response = requests.post(log_analytics_query_url, json=post_body, headers=headers)
general_query_json = general_query_response.json()

# Create the output table and table headers row
table_data_query = []
table_columns = []
for column in general_query_json['tables'][0]['columns']:
    table_columns.append(column['name'])

table_columns[2] = "Available Time"
table_columns[3] = "Last Available"
table_columns[4] = "Avg CPU (%)"
table_columns[5] = "Max CPU (%)"
table_columns[6] = "Free Disk Space (%)"
table_columns[7] = "Avg RAM (GB)"
table_columns[8] = "Min RAM (MB)"
table_columns[9] = "Method"
table_columns.insert(6, "CPU Bottlenecks")
table_data_query.append(table_columns)

# Create a progress bar instance for the VM loop
widgets = [' [',
         progressbar.Timer(format= 'elapsed time: %(elapsed)s'),
         '] ',
           progressbar.Bar('*'),' (',
           progressbar.ETA(), ') ',
          ]

bar = progressbar.ProgressBar(max_value=len(general_query_json['tables'][0]['rows']), widgets=widgets).start()

# Loop all VMs from result to get bottleneck timestamps and modify the table columns
for i in range(len(general_query_json['tables'][0]['rows'])):
    row = general_query_json['tables'][0]['rows'][i]
    vm_name = row[0]
    max_cpu = math.floor(row[5])
    reporting_method = row[9]
    usage_hours = row[2] // 60
    usage_minutes = row[2] % 60
    row[2] = f"{usage_hours}h {usage_minutes}m"
    last_hb_date = row[3].split('.')[0]
    row[3] = (datetime.strptime(last_hb_date, '%Y-%m-%dT%H:%M:%S')).strftime("%c")
    
    # Run bottleneck query in Log Analytics
    vm_post_body = {}
    if reporting_method == "Insights":
        vm_post_body = {
   	        "query": f"let vm_name = '{vm_name}'; \
                        let cpu_value = {max_cpu}; \
                        let metrictimespan = ago({query_period}d); \
                        InsightsMetrics \
                        | where TimeGenerated > metrictimespan \
                        | where Computer == vm_name \
                        | where Name == 'UtilizationPercentage' \
                        | where Val >= cpu_value \
                        | summarize CPU = avg(Val) by bin(TimeGenerated, 15m), Computer \
                        | join kind=leftouter (InsightsMetrics \
                            | where TimeGenerated > metrictimespan and Name == 'AvailableMB' and Computer == vm_name \
                            | summarize Memory = avg(Val) by bin(TimeGenerated, 15m), Computer) \
                        on Computer, TimeGenerated, $left.Computer == $right.Computer, $left.TimeGenerated == $right.TimeGenerated \
                        | project TimeGenerated, Computer, CPU, Memory" 
        }
    else:
        vm_post_body = {
   	        "query": f"let vm_name = '{vm_name}'; \
                        let cpu_value = {max_cpu}; \
                        let metrictimespan = ago({query_period}d); \
                        Perf \
                        | where TimeGenerated > metrictimespan \
                        | where Computer == vm_name \
                        | where CounterName == '% Processor Time' \
                        | where CounterValue >= cpu_value \
                        | summarize avg(CounterValue) by bin(TimeGenerated, 15m), Computer \
                            | join kind=leftouter (Perf \
                            | where CounterName == 'Available MBytes Memory' or CounterName == 'Available MBytes' or CounterName == 'Available Bytes' \
                            | extend AvailableMbytes = case(CounterName == 'Available Bytes', CounterValue/1048576, CounterValue) \
                            | summarize avg(AvailableMbytes) by bin(TimeGenerated, 15m), Computer) \
                        on Computer, TimeGenerated, $left.Computer == $right.Computer, $left.TimeGenerated == $right.TimeGenerated \
                        | project TimeGenerated, Computer, CPU = avg_CounterValue, Memory = avg_AvailableMbytes" 
        }
    vm_query_response = requests.post(log_analytics_query_url, json=vm_post_body, headers=headers)
    vm_query_json = vm_query_response.json()
    row.insert(6, "")
    
    # Append to table
    for results in vm_query_json['tables'][0]['rows']:
        row[6] += f"{results[0]} "
    table_data_query.append(row)
    bar.update(i)
    
# Print final table
print(tabulate(table_data_query, headers='firstrow', tablefmt='psql', floatfmt=".2f", maxcolwidths=[None, None, 14, None, None, None, 20]))
