from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk import util
from datetime import datetime
import time
import json
import typing
import copy
import requests

dev_var = Variables()
context = Variables.task_call(dev_var)

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]

#########################################################
# Function: Parse all MS values recursivly for the given field
def data_find_migrate_recursif(orig_field_name, fields, ms_newvalues):
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
               data_find_migrate_recursif(orig_field_name, copy.deepcopy(fields), value1[field]) 
             else:
               if value :
                 context['Filter_'+orig_field_name+'_field_values'][value] = ''
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
