import json
import typing
import os

import os.path

import time

import pandas as Pandas
from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()


context = Variables.task_call(dev_var)

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]

#check if the folder  DIRECTORY exist, else create it
if not os.path.isdir(DIRECTORY):
 os.mkdir(DIRECTORY)

timeout = 3600


#########################################################
# Function: Run the MS import and store the result
def run_microservice_import():
  global ms_to_run, previous_ms_to_run, MS_list_run, previous_ms_data, full_message, params, timeout, parameter1_to_give_to_ms, object_id,MS_list_not_run, nb_ms_to_run, device_id_full, dest

  nb_ms_to_run = nb_ms_to_run + 1 

  if ms_to_run != previous_ms_to_run :
    previous_ms_to_run = ms_to_run
    MS_list_run[ms_to_run] = 1
    if previous_ms_data:
      full_message = full_message +  printTable(previous_ms_data)
      previous_ms_data = []
    full_message = full_message + '\n\n############# For '+ dest + ' device,  MS '+ ms_to_run +  ' ############# \n'
  obmf.command_execute('IMPORT', params, timeout) #execute the MS to get new status
  response = json.loads(obmf.content)
  #context['ms_status_import_response_'+ms_to_run] = response #   "message ="{\"arp_summary\":{\"274f9f441f0dd0bc3ab2af14ef7bc6d5\":{\"total\":\"7\",\"incomplete\":\"0\"}}}",

  if (response.get("status") and response["status"] == "OK") or (response.get("wo_status") and response["wo_status"] == "OK"):
     if response.get("status"):
       message =  response["message"]
     else:
       message =  response["wo_newparams"]
     message = json.loads(message)
     if message.get(ms_to_run):
       message = message[ms_to_run]
       if isinstance(message, dict):
         for key2,val2 in message.items():
           previous_ms_data.append(val2)
       else:
         previous_ms_data.append(message)
  else:
    if response.get("wo_newparams"):
      wo_newparams =  response["wo_newparams"]
      if 'An update is already running' in wo_newparams:
        msg = 'SMS ERROR: on device '+device_id_full+' can not run MS '+ ms_to_run + ' : '+ str(wo_newparams)
        create_event(device_id_full, "1", "MIGRATION", "STATUS",  subtenant_ref, subtenant_id, msg)
        MSA_API.task_error(msg , context, True)
    MS_list_not_run[ms_to_run]=1
 
start_sec  = time.time()            
nb_ms_to_run = 0   

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
  msg = 'Can not open file "' + file + '"'
  create_event(device_id_full, "1", "MIGRATION", "STATUS",  subtenant_ref, subtenant_id, msg)
  MSA_API.task_error(msg, context, True)
  data_list = ''    
  
context['status_liste'] = data_list
context['status_liste_file_full'] = file 

wf_fields = {}
warning = ""

devices = {}
devices['Source'] = context['source_device_id']
devices['Destination'] = context['destination_device_id']

if not context.get('pushed_to_destination_device') or context['pushed_to_destination_device'] != 'true':
 migrate = 'before'
else:
 migrate = 'after'

for  dest, device_id_full in devices.items(): 

  device_id = device_id_full[3:]
  
  full_message = '\n#####################################################################################################\n'
  full_message = full_message +  '  For '+ dest + ' device ('+device_id_full +') ' + migrate + ' migration\n'
  full_message = full_message +  '#####################################################################################################\n\n'


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
  #context['MS_attached source device_id' + device_id + ' : '] = all_ms_attached
  #all_ms_attached = {"id" : 44, ..."microserviceUris" : { "CommandDefinition/LINUX/CISCO_IOS_emu  },  "CommandDefinition/LINUX/CISCO_IOS_emulation/bgp_vrf.xml" : {  "name" : "bgp_vrf",   "groups" : [ "EMULATION", "CISCO", "IOS" ].....
  MS_list = []
  MS_list_run = {}
  MS_list_not_run = {}


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
  MS_list_run = {}
  MS_list_not_run = {}

  if all_ms_attached:
    for full_ms, MS in all_ms_attached.items():
      if Path(full_ms).stem:
        MS_list.append(Path(full_ms).stem)  # Path(full_ms).stem = MS filename without extension 
   
  previous_ms_to_run = ''
  previous_ms_data = []

  if data_list:
    for line in data_list:
      if (not line.startswith('#')) and line.strip():
        list = line.split('|')  

        # device source ou destination|ms_source|ms_source_field1|ms_source_field2|MS_to_run|parameter1_to_give_to_MS|parameter2_to_give_to_MS
        #  interface|object_id|None|interface_status|object_id|None
        #  bgp_vrf|object_id|neighbor.0.bgp_vrf_neighbor|bgp_neighbor_status|object_id|ip_bgp_neighbor          
        if len(list) > 6:
          device_src_dest          = list[0]
          ms_source                = list[1]
          ms_source_field1         = list[2]
          ms_source_field2         = list[3]
          ms_to_run                = list[4]
          parameter1_to_give_to_ms = list[5]
          parameter2_to_give_to_ms = list[6]

          if device_src_dest == dest:
            if ms_source != 'None' and context.get(ms_source+'_values') and context[ms_source+'_values'] :
              '''  "bgp_vrf_values": {
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

              full_source_field = ms_source+'_'+ms_source_field1+'_'+ms_source_field2
              context['Status_'+full_source_field+'_field_values'] = {}
              context['Status_'+full_source_field+'_list'] = list
              values_to_send = {}
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
                                   key =  field1_value+'|'+value2[field_lev2] #used key to not get many times the same values                         
                                   values_to_send[key] = new_value
                                   new_value                   = {}
                                   new_value[parameter1_to_give_to_ms] = field1_value

                       else:
                         values_to_send[field1_value] = new_value
                         
              # values_to_send: { {  "object_id": "TRIBUNAL-JUSTICA",  "ip_bgp_neighbor": "187.93.7.58" },{"object_id": "TRIBUNAL-JUSTICA"...
              #context['Status_'+full_source_field+'_field_values333'] = values_to_send              


              for key1, values in values_to_send.items():
                ms_input = {}
                object_id =''
                for key,val in values.items():
                  ms_input[key] = val
                  if key == 'object_id':
                    object_id = val
                obj               = {}
                obj[object_id]    = ms_input  
                params            = {}
                params[ms_to_run] = obj 
                # Run the MS import and store the result
                run_microservice_import()

            elif ms_source == 'None' and ms_to_run:
              #Run IMPORT for the give MS to update the DB
              ms_input = {}
              #ms_input['test'] = 'test'
              obj = {"":ms_input}  
              #obj['test'] = ms_input  
              obj[''] = ms_input  
              params = {}
              params[ms_to_run] = obj 
              # Run the MS import and store the result
              run_microservice_import()
            else:
              warning = warning + "\n the Micros service "+ms_source+" is no attached to the device "+ device_id_full


  if previous_ms_data:
    full_message = full_message +  printTable(previous_ms_data)
  if MS_list_run:
    MS_list_run             = ', '.join(MS_list_run.keys())  
  else:
    MS_list_run = ''
  if MS_list_not_run:
    MS_list_not_run             = ', '.join(MS_list_not_run.keys())  
  else:
    MS_list_not_run = ''  
      

  now = datetime.now() # current date and time
  day = now.strftime("%m-%d-%Y-%Hh%M")
  
  #Create the global config file :
  generate_file = DIRECTORY+ "/" + "ALL_SOURCE_STATUS_"  + dest.lower() +'_' + migrate + '_' + day + '.txt'
  context['generate_'+dest.lower() +'_' + migrate + '_status_file'] = generate_file

  f = open(generate_file, "w")
  f.write(full_message)
  f.close()
    
end_sec  = time.time()   
         
exec_sec = int(end_sec - start_sec) 
   
if MS_list_not_run:    
  MSA_API.task_success('DONE in '+str(exec_sec)+' sec: for devices status for ' + ' and '.join(devices.keys()) + ', but can not get status for (' + MS_list_not_run + ') but get the status for ('+MS_list_run+') run '+str(nb_ms_to_run)+ ' MS with differents parameters', context, True)
else:
  MSA_API.task_success('DONE in '+str(exec_sec)+' sec: Get Status for ' + ' and '.join(devices.keys()) + '  ('+MS_list_run+'), run '+str(nb_ms_to_run)+ ' MS with differents parameters', context, True)



