import json
import typing
import os
from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()

context = Variables.task_call(dev_var)

timeout = 3600

device_id_full = context['source_device_id_full']
device_id      = device_id_full[3:]

# instantiate device object
obmf  = Order(device_id=device_id)

context['customer_id_instance_id'] =  context['customer_id'] + '_#' +context['SERVICEINSTANCEID']

#we synchronise all MS attached to the source device because some MS are intermediated and need to be synchronized with good order.
create_event(device_id_full, "5", "1", subtenant_ref, subtenant_id, "START IMPORT")

obmf.command_synchronize(timeout)
responses = json.loads(obmf.content)
context[ 'ALL source MS_synch_values for '+device_id] = responses
if isinstance(responses, dict) and responses.get("wo_status") and responses["wo_status"] == "FAIL":
  MSA_API.task_error('Can not synchronise device '+ device_id_full + ' : '+responses['wo_newparams'], context, True)
  
MS_list = []
if isinstance(responses, typing.List): 
  #responses contains only MS which contains some datas, we don't get attached MS without datas
  for response in responses:
    # "commandId": 0, "status": "OK","message": "{\"class_map\":{\"RT\":{\"object_id\":\"RT\",\"matches\":{\"0\":{\"not\":\"\",\"match_cmd\":\"ip \"}}}},\"ip_route\"
    if response.get('message') and response.get('status'):
      if response['status'] != 'OK':
        MSA_API.task_error('ERROR: during synchronise. Managed entity Id: '+ device_id_full + ' : ' + str(response), context, True)
      else:
        response_message = json.loads(response.get('message'))  #convert into json array
        for MS in response_message:
          if response_message.get(MS):
            #MS_list.append(MS)
            context[ MS + '_values'] = response_message.get(MS)
          else:
            context[ MS + '_values'] = response_message
            
            
  # Get deployment settings ID for the device.
  deployment_settings_id = obmf.command_get_deployment_settings_id()
  context['source_deployment_settings_id_'+device_id_full] = deployment_settings_id
  
  #Get all microservices attached to this deployment setting.
  confprofile  = ConfProfile(deployment_settings_id)
  all_ms_attached = confprofile.read()
  all_ms_attached = json.loads(all_ms_attached)
  if all_ms_attached.get("microserviceUris"):
    all_ms_attached = all_ms_attached["microserviceUris"] 
  context['MS_attached source device_id' + device_id + ' : '] = all_ms_attached
  #all_ms_attached = {"id" : 44, ..."microserviceUris" : { "CommandDefinition/LINUX/CISCO_IOS_emu  },  "CommandDefinition/LINUX/CISCO_IOS_emulation/bgp_vrf.xml" : {  "name" : "bgp_vrf",   "groups" : [ "EMULATION", "CISCO", "IOS" ].....
     
  if all_ms_attached:
    for full_ms, MS in all_ms_attached.items():
      if Path(full_ms).stem:
        MS_list.append(Path(full_ms).stem)    # Path(full_ms).stem = MS filename without extension
   
if MS_list:
  MS_list             = ';'.join(MS_list)  
  context['MS_list']  = MS_list
else:
  MS_list = ''
    
    
    
MSA_API.task_success('DONE: all MS attached to the managed entity: '+ device_id_full + ' imported ('+MS_list+')', context, True)



