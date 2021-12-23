import json
import typing
import os
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()
dev_var.add('source_device_id', var_type='Device')
dev_var.add('source_interfaces_name', var_type='String')
dev_var.add('destination_device_id', var_type='Device')
dev_var.add('destination_interfaces_name', var_type='String')
dev_var.add('customer_id', var_type='String')
#dev_var.add('MS_list', var_type='String')
dev_var.add('link.0.MicroService', var_type='String')
dev_var.add('link.0.file_link', var_type='Link')

context = Variables.task_call(dev_var)

timeout = 600

#get device_id from context
device_id = context['source_device_id'][3:]

# instantiate device object
obmf  = Order(device_id=device_id)


MS_source_path = context['MS_source_path']

#we synchronise all MS attached to the source device because some MS are intermediated and need to be synchronized with good order.
obmf.command_synchronize(timeout)
responses = json.loads(obmf.content)
MS_list = []
if isinstance(responses, typing.List): 
  #context[ 'ALL MS_synch_values'] = responses
  #responses contains only MS which contains some datas, we don't get attached MS without datas
  for response in responses:
    # "commandId": 0, "status": "OK","message": "{\"class_map\":{\"RT\":{\"object_id\":\"RT\",\"matches\":{\"0\":{\"not\":\"\",\"match_cmd\":\"ip \"}}}},\"ip_route\"
    if response.get('message') and response.get('status'):
      if response['status'] != 'OK':
        MSA_API.task_error('Error during synchronise DeviceId:'+context['source_device_id'] + ' : ' + str(response), context, True)
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
  context['source_deployment_settings_id'] = deployment_settings_id
  
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
      if MS.get('name'):
        MS_list.append(MS['name'])
   
  if MS_list:
    MS_list             = ';'.join(MS_list)  
    context['MS_list']  = MS_list
  else:
    MS_list = ''
    
    
    
MSA_API.task_success('Good, all MS attached to the device DeviceId:'+context['source_device_id'] + ' imported ('+MS_list+')', context, True)



