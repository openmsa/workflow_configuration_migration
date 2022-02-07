import json
import typing
import os
from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()

dev_var.add('source_device_id')

context = Variables.task_call(dev_var)

context['real_or_simul_device'] = 'real'
   
timeout = 600

#read import_WF_parameters_into_MS.txt file
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../'+context['get_devices_status_file']   # get_devices_status.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  import_liste = file1.read()
  file1.close()
  data_list = import_liste.split('\n')
  data_list = [i for i in data_list if i] #remove empty element
else:
  data_list = ''    
  
context['status_liste'] = data_list
context['status_liste_file_full'] = file 

wf_fields = {}
warning = ""



#get device_id from context
device_id_full = context['source_device_id']
device_id = device_id_full[3:]
# instantiate device object
obmf  = Order(device_id=device_id)
       
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
MS_list = []
if all_ms_attached:
  for full_ms, MS in all_ms_attached.items():
    if Path(full_ms).stem:
      MS_list.append(Path(full_ms).stem)  # Path(full_ms).stem = MS filename without extension 
 
if data_list:
  for line in data_list:
    if (not line.startswith('#')) and line.strip():
      list = line.split('|')  
      #  ms_source|ms_source_field1|ms_source_field2|MS_to_run|parameter1_to_give_to_MS|parameter2_to_give_to_MS
      #  interface|object_id|None|interface_status|object_id|None
      #  bgp_vrf|object_id|neighbor.0.bgp_vrf_neighbor|bgp_neighbor_status|object_id|ip_bgp_neighbor          
      if len(list) > 2:
        ms_source                = list[0]
        ms_source_field1         = list[1]
        ms_source_field2         = list[2]
        ms_to_run                = list[3]
        parameter1_to_give_to_ms = list[4]
        parameter2_to_give_to_ms = list[5]
        
        if context.get(ms_source+'_values') and context[ms_source+'_values']:
          ''' "interface_values": {
                "Port-channel1": {
                    "object_id": "Port-channel1",
                    "type": "Port-channel",
                    
           "bgp_vrf_values": {
             "TRIBUNAL-JUSTICA": {
                    "object_id": "TRIBUNAL-JUSTICA",
                    "neighbor": {
                        "0": {
                            "bgp_vrf_neighbor": "187.93.7.58",
                            "bgp_vrf_neighbor_remote_as": "65001"
                        },
          '''
          all_values_to_test=[]
          field1_values={}
          if (ms_source_field1 == 'object_id'):
            #fields = ms_source_field1.split('.0.')
            full_source_field = ms_source+'_'+ms_source_field1
            context['Status_'+full_source_field+'_field_values'] = {}
            context['Status_'+full_source_field+'_list'] = list
            values_to_send = []
            ## Find all source values
            ms_values = context[ms_source+'_values']
            if isinstance(ms_values, dict):
              for  key, value1 in ms_values.items():
                if isinstance(value1, dict):
                  if value1.get(ms_source_field1):
                     field1_value                = value1[ms_source_field1]
                     new_value                   = {}
                     new_value[parameter1_to_give_to_ms] = field1_value
                     if ms_source_field2 and ms_source_field2 != 'None':
                       fields = ms_source_field2.split('.0.')
                       if isinstance(fields, typing.List) and fields and len(fields) > 1:
                         field_lev1 = fields[0]
                         field_lev2 = fields[1]
                         if value1.get(field_lev1):
                           value_lev1 = value1[field_lev1]
                           if isinstance(value_lev1, dict):
                             for  key2, value2 in value_lev1.items():
                               if value2.get(field_lev2):
                                 new_value[parameter2_to_give_to_ms] = value2[field_lev2]                               
                                 values_to_send.append(new_value)
                                 new_value                   = {}
                                 new_value[parameter1_to_give_to_ms] = field1_value

                     else:
                       values_to_send.append(new_value)
                       
                       
            context['Status_'+full_source_field+'_field_values'] = values_to_send              
  
            #Run IMPORT for the give MS to update the DB
            ms_input = {}
            obj = {"":ms_input}  
            params = {}
            params[ms_to_run] = obj 
            obmf.command_execute('IMPORT', params, timeout) #execute the MS to get new status

  
            for values in values_to_send:
              ms_input = {}
              for key,val in values.items():
                ms_input[key] = val
    
                obj = {"":ms_input}  
                params = {}
                params[ms_to_run] = obj 
                context['ms_params_'+ms_to_run+'_'+parameter1_to_give_to_ms] = params
                obmf.command_execute('READ', params, timeout) #execute the MS to get new status
                response = json.loads(obmf.content)
                context['ms_params_response_'+ms_to_run+'_'+parameter1_to_give_to_ms] = response 

          else:
            warning = warning + "\n the first field should be object_id instead of '" +ms_source_field1+"'"
        else:
          warning = warning + "\n the Micros service "+ms_source+" is no attached to the device "+ device_id_full
       
if MS_list:
  MS_list             = ';'.join(MS_list)  
else:
  MS_list = ''
    
MSA_API.task_success('DONE: Get Status for '+ device_id_full + ' ('+MS_list+')', context, True)



