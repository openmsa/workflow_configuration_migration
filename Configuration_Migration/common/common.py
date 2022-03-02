from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk import util
from msa_sdk.order import Order
from datetime import datetime
import time
import json
import typing
import copy
import requests
import ipaddress
import re
import pandas as Pandas

dev_var = Variables()
context = Variables.task_call(dev_var)

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]

#########################################################
# Function: to convert 
def printTable(myDict):
  df = Pandas.DataFrame.from_records(myDict)
  return df.to_string()

#########################################################
# Function: Run the MS import and store the result
def run_microservice_import():
  global ms_to_run, previous_ms_to_run, MS_list_run, previous_ms_data, full_message, params, timeout, parameter1_to_give_to_ms, object_id,MS_list_not_run
  if ms_to_run != previous_ms_to_run :
    previous_ms_to_run = ms_to_run
    MS_list_run[ms_to_run] = 1
    if previous_ms_data:
      full_message = full_message +  printTable(previous_ms_data)
      previous_ms_data = []
    full_message = full_message + '\n\n############# from MS '+ ms_to_run +  ' ############# \n'
  obmf.command_execute('IMPORT', params, timeout) #execute the MS to get new status
  response = json.loads(obmf.content)
  context['ms_status_import_response_'+ms_to_run] = response #   "message ="{\"arp_summary\":{\"274f9f441f0dd0bc3ab2af14ef7bc6d5\":{\"total\":\"7\",\"incomplete\":\"0\"}}}",

  if response.get("status") and response["status"] == "OK":
     message =  response["message"]
     message = json.loads(message)
     if message.get(ms_to_run):
       message = message[ms_to_run]
       if isinstance(message, dict):
         for key2,val2 in message.items():
           previous_ms_data.append(val2)
       else:
         previous_ms_data.append(message)
  else:
    #MSA_API.task_error('ERROR: Cannot run CREATE on microservice: '+ ms_to_run + ', response='+ str(response) , context, True)
    MS_list_not_run[ms_to_run]=1
    

#########################################################
# Function: Parse all MS values recursively for the given field
def data_find_migrate_recursive(orig_field_name, fields, ms_newvalues):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
  if field:
    if isinstance(ms_newvalues, dict):
      for  key, value1 in ms_newvalues.items():
        if isinstance(value1, dict):
          if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               data_find_migrate_recursive(orig_field_name, copy.deepcopy(fields), value1[field]) 
             else:
               if value :
                 context['Filter_'+orig_field_name+'_field_values'][value] = ''
  return 'not found'

#########################################################
# Function: Parse all MS values recursivly for the given field
def change_interfaces_names_recursif(source_field, fields, ms_newvalues, new_interfaces_names, new_interfaces_names_clean):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
    
  if field:
    if isinstance(ms_newvalues, dict):
      if field == 'KEY':
        for old_interface_name, new_interface_name in new_interfaces_names_clean.items():
          if ms_newvalues.get(old_interface_name):
            ms_newvalues[new_interface_name] = ms_newvalues[old_interface_name]
            del ms_newvalues[old_interface_name] 
      else: 
        for  key, value1 in ms_newvalues.items():
          if isinstance(value1, dict):
            if value1.get(field):
               value = value1[field]
               if isinstance(value, dict):
                 change_interfaces_names_recursif(source_field, copy.deepcopy(fields), value1[field], new_interfaces_names, new_interfaces_names_clean) 
               else:
                 if value :
                   if new_interfaces_names.get(value):
                     ms_newvalues[key][field] = new_interfaces_names[value]

  return 'not found'

#########################################################
# Function: Parse all MS values recursivly for the given field
def find_all_ip_in_subnet(interface_name, ipv4_address, ipv4_mask, interfaces_IP_available):
  if ipv4_address and ipv4_mask:
    # convert ipv4 subnet mask to cidr notation 
    len = ipaddress.IPv4Network('0.0.0.0/'+ipv4_mask).prefixlen  #24 
    cidr = ipv4_address+'/'+str(len)
    context['cidr_'+ipv4_address+'/'+ipv4_mask ] =  cidr    # "cidr_": "200.207.251.229/30"
    ips = ipaddress.ip_network(cidr, strict=False)
    ip_list = [str(ip) for ip in ips]    
    for ip in ip_list:
      interfaces_IP_available[str(ip)] = interface_name
    
  return interfaces_IP_available
 
#########################################################
# Function: Parse all MS values recursivly for the given field
def remove_bad_ip_values_recursif(orig_field_name, fields, ms_newvalues, interfaces_IP_available):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
  if field:
    if isinstance(ms_newvalues, dict):
      ms_newvalues2 = copy.deepcopy(ms_newvalues) 
      # We can not remove one element while iterating over it, so itirating on one copy ms_newvalues2
      for  key, value1 in ms_newvalues2.items():
      
        if isinstance(value1, dict):
          if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               remove_bad_ip_values_recursif(orig_field_name, copy.deepcopy(fields), ms_newvalues[key][field], interfaces_IP_available) 
             else:
               if value:
                 match = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", value)
                 if bool(match) and value not in interfaces_IP_available:
                   #ms_newvalues[key][field]  = 'IP_TO_REMOVE for '+orig_field_name+ ', value='+value
                   ms_newvalues.pop(key)  #remove parent value
                 #else: 
                   #ms_newvalues[key][field]  = 'OK TO KEEP for '+orig_field_name+ ', value='+value
                 
  return 'not found'

#########################################################
# Function: Parse all MS values recursivly for the given field
def remove_bad_values_recursif(destination_field_name, fields, ms_newvalues, available_values):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
  if field:
    if isinstance(ms_newvalues, dict):
      ms_newvalues2 = copy.deepcopy(ms_newvalues) 
      # We can not remove one element while iterating over it, so itirating on one copy ms_newvalues2
      for  key, value1 in ms_newvalues2.items():
      
        if isinstance(value1, dict):
          if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               remove_bad_values_recursif(destination_field_name, copy.deepcopy(fields), ms_newvalues[key][field], available_values) 
             else:
               if value:
                 if  value not in available_values:
                   #ms_newvalues[key][field]  = 'IP_TO_REMOVE_value='+value
                   ms_newvalues.pop(key)  #remove parent value
                 #else: 
                   #ms_newvalues[key][field]  = 'OK TO KEEP_value='+value
                 
  return 'not found'


def create_event(device_id, severity, type_id, subtenant_ref, subtenant_id, message):
	username='superuser'
	password='x^ZyuGM6~u=+fY2G'
	dateTimeObj = datetime.now()
	format = "%Y-%m-%dT%H:%M:%S+0000"
	time1 = dateTimeObj.strftime(format)
	format = "%Y-%m-%d"
	date = dateTimeObj.strftime(format)
	timestamp = datetime.timestamp(dateTimeObj)
	url = "http://msa_es:9200/ubilogs-"+date+"/_doc"
	#util.log_to_process_file(process_id, url)
	payload = {"rawlog": ""+message+"", "device_id": ""+device_id+"", "timestamp": ""+str(timestamp)+"", "date": ""+time1+"", "customer_ref": ""+subtenant_ref+"", "customer_id": ""+subtenant_id+"", "severity": ""+severity+"", "type": ""+type_id+"", "subtype": "WF"}
	#util.log_to_process_file(process_id, payload)
	headers = {'content-type': 'application/json'}
	result = requests.post(url, auth=(username, password), json=payload, headers=headers)
	
	return result
