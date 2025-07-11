import json
import typing
import os
import re
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
MS_TO_GET_VRF_VALUES    = 'interface'
FIELD_TO_GET_VRF_VALUES = 'vrf_name'

#########################################################
# Function: Run the MS import and store the result
def run_microservice_import():
  global ms_to_run, previous_ms_to_run, MS_list_run, previous_ms_data, full_message, params, timeout, parameter1_to_give_to_ms, object_id,MS_list_not_run, nb_ms_to_run, device_id_full, status_to_run, MS_attached_list

  nb_ms_to_run = nb_ms_to_run + 1 
  previous_ms_data = []
    
  if ms_to_run != previous_ms_to_run :

    if previous_ms_to_run and previous_ms_to_run not in MS_attached_list.keys():
      full_message = full_message + 'The MS "'+previous_ms_to_run+'" is not linked to this device, add this MS in the deployment setting for this device\n'
    
    full_message = full_message + '\n\n###############################################################################################\n####################### For '+ status_to_run + ' device,  MS '+ ms_to_run + ' #######################\n###############################################################################################\n'
    previous_ms_to_run = ms_to_run
    MS_list_run[ms_to_run] = 1
  
  if ms_to_run in MS_attached_list.keys(): 
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
 
  #calcul the command to run on the device:
  command_to_run_on_device = calcul_command_to_run_on_device(params)  
  full_message = full_message + '\n# Commands on device: ' +str(command_to_run_on_device)+" \n#################################################################################\n"

  #if previous_ms_data and previous_ms_to_run in MS_attached_list.keys():
  if previous_ms_data:
    full_message = full_message +  printTable(previous_ms_data) +'\n'

 
def calcul_command_to_run_on_device(params):
  global MS_attached_list
  orig_command =''
  all_commands=[]  
  # params = {'interface_status': {'GigabitEthernet0/0/2': {'object_id': 'GigabitEthernet0/0/2'}}}" 
  # params = {'bgp_received_routes': {'10429': {'object_id': '10429', 'neighbor': '189.20.5.158'}}
  all_commands=[]  
  for ms, allvalues in params.items():
    if MS_attached_list.get(ms):
      filename = '/opt/fmc_repository/'+MS_attached_list[ms]
      file_one = open(filename, "r")
      import_command=''
      for line in file_one:
        if re.search('<operation>', line):
          import_command = line
      file_one.close()
      # import_command= <operation><![CDATA[{if isset($params.neighbor)}/config/extract_part_of_simulated_file.py /config/cisco_ios/test.status "show ip bgp neighbors {$params.neighbor} advertised-routes" {/if}]]></operation>
      orig_command = re.search('show (.+?)]]',import_command)
      if not orig_command or not orig_command.group(0):
        orig_command = re.search('ping (.+?)]]',import_command)
      if  orig_command and orig_command.group(0):
        orig_command = orig_command.group(0) #full command
        orig_command = orig_command.replace("{/if}]]",'') 
        orig_command = orig_command.replace("]]",'') 
        orig_command = re.sub(r"\s+$", '', orig_command) 
        orig_command = re.sub(r"\"$", '', orig_command) 
        
        # orig_command = "show ip bgp neighbors {$params.neighbor}" 
        all_commands=[]  
        for obj, values in allvalues.items():
          line = orig_command
          for key, value in values.items():
            # key = neighbor and value = 189.20.5.158
            line = line.replace('{$params.'+key+'}',value)
          all_commands.append(line)   

  command = orig_command
  return '"'+'" \n#"'.join(all_commands)+ '"'
  
  
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
  
#context['status_liste'] = data_list
context['status_liste_file_full'] = file 

wf_fields = {}
warning = ""

devices = {}
devices['source'] = context['source_device_id_full']
devices['destination'] = context['destination_device_id_full']

customer=context['customer_id_instance_id']

for  status_to_run, device_id_full in devices.items(): 

  full_message = '\n#####################################################################################################\n'
  full_message = full_message + '############# WF Instance : ' + customer +  ' ############# \n'
  full_message = full_message + '#####################################################################################################\n'
  full_message = full_message + '\n#####################################################################################################\n'
  if context.get('destination_device_type') and context['destination_device_type']:
    migrate = 'simulated'
    full_message = full_message +  '  For '+ context['destination_device_type'] + ' ' + status_to_run + ' device ('+device_id_full +')\n'
  else:
    if context.get('pushed_to_destination_device') and context['pushed_to_destination_device'] == 'true':
      migrate = 'after'
    else:
      migrate = 'before'
    full_message = full_message +  '  For ' + status_to_run + ' device ('+device_id_full +') ' + migrate + ' migration\n'
     
  full_message = full_message +  '#####################################################################################################\n\n'


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
  #context['MS_attached source device_id' + device_id + ' : '] = all_ms_attached
  #all_ms_attached = {"id" : 44, ..."microserviceUris" : {  "CommandDefinition/LINUX/CISCO_IOS_emulation/bgp_vrf.xml" : {  "name" : "bgp_vrf",   "groups" : [ "EMULATION", "CISCO", "IOS" ].....
  MS_attached_list = {}
  MS_list_run = {}
  MS_list_not_run = {}

  if all_ms_attached:
    for full_ms, MS in all_ms_attached.items():
      if Path(full_ms).stem:
        MS_attached_list[Path(full_ms).stem] = full_ms  # Path(full_ms).stem = MS filename without extension 
   
  previous_ms_to_run = ''
  previous_ms_data = []
  
  if data_list:
    for line in data_list:
      if (not line.startswith('#')) and line.strip():
        list = line.split('|')  

        #need_vrf|device source or destination|ms_source|ms_source_field1|ms_source_field2|MS_to_run|parameter1_to_give_to_MS|parameter2_to_give_to_MS        
        if len(list) > 7:
          need_vrf                = list[0].lower()
          device_src_dest          = list[1].lower()
          ms_source                = list[2]
          ms_source_field1         = list[3]
          ms_source_field2         = list[4]
          ms_to_run                = list[5]
          parameter1_to_give_to_ms = list[6]
          parameter2_to_give_to_ms = list[7]

          if device_src_dest == status_to_run:
            #check if we have on vrf value in the interface MS:
            existing_vrf = 0
            if (need_vrf  != 'none') and (need_vrf  != 'all'):
              interface_values = json.loads(context[MS_TO_GET_VRF_VALUES+'_values_serialized'])
              if interface_values:
                for id, interface in interface_values.items():
                  if interface.get(FIELD_TO_GET_VRF_VALUES) and interface[FIELD_TO_GET_VRF_VALUES]:
                    existing_vrf = 1
                  
            if (need_vrf  == 'all' or (need_vrf == 'no_vrf_value' and existing_vrf == 0) or (need_vrf == 'need_vrf_value' and existing_vrf == 1)):
              if ms_source != 'None' and context.get(ms_source+'_values_serialized') and context[ms_source+'_values_serialized'] :
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
                ms_values = json.loads(context[ms_source+'_values_serialized'])
                if isinstance(ms_values, dict):
                  for  key, value1 in ms_values.items():
                    if isinstance(value1, dict):
                      if value1.get(ms_source_field1):
                         field1_value                = value1[ms_source_field1]
                         new_value                   = {}
                         if parameter1_to_give_to_ms == "object_id_physical_interface":
                           #for interface status, we should give th interface instead of subinterface name
                           new_value["object_id"] = re.sub('\.\d+$', '', field1_value)
                         else:
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
                                     if parameter1_to_give_to_ms == "object_id_physical_interface":
                                       new_value["object_id"] = re.sub('\.\d+$', '', field1_value)
                                     else:
                                       new_value[parameter1_to_give_to_ms] = field1_value
                               else:
                                 new_value = value_lev1
                           else:
                            
                            if value1.get(ms_source_field2):
                              new_value[parameter2_to_give_to_ms] = value1[ms_source_field2]
                              if parameter1_to_give_to_ms == "object_id_physical_interface":
                                values_to_send["object_id"] = re.sub('\.\d+$', '', new_value)
                              else:
                                values_to_send[parameter1_to_give_to_ms] = new_value
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
                ms_input['object_id'] = 'need_for_import'
                obj = {}  
                obj['need_for_import'] = ms_input  # need at leat one value for the import
                params = {}
                params[ms_to_run] = obj 
                # Run the MS import and store the result
                run_microservice_import()
            else:
              #no run this MS because the VRF condition is not valide
              ms_to_run = previous_ms_to_run 
              
          else:
            warning = warning + "\n the Micros service "+ms_source+" is no attached to the device "+ device_id_full


  if previous_ms_data and ms_to_run in MS_attached_list.keys():
    #context['status_res_'+ms_to_run+'_values_serialized2'] = json.dumps(previous_ms_data)
    full_message = full_message +  printTable(previous_ms_data)
  elif ms_to_run and ms_to_run not in MS_attached_list.keys():
    full_message = full_message + 'The MS "'+ms_to_run+'" is not linked to this device, add this MS in the deployment setting for this device'
    
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
  generate_file = DIRECTORY+ "/" + status_to_run.lower() + "_"+ migrate +"_device_status_#" + context['SERVICEINSTANCEID'] + '_' + day + '.txt'
  context['generate_'+status_to_run.lower() +'_' + migrate + '_status_file'] = generate_file

  f = open(generate_file, "w")
  f.write(full_message)
  f.close()
    
end_sec  = time.time()   
         
exec_sec = int(end_sec - start_sec) 
   
if context.get('destination_device_type') and context['destination_device_type']:
  message = migrate
else:
  message = migrate + ' migration,'

if MS_list_not_run:    
  MSA_API.task_success('DONE in '+str(exec_sec)+' sec: for devices status for ' + ' and '.join(devices.keys()) + ' '+ message + ' devices but can not get status for (' + MS_list_not_run + ') but get the status for ('+MS_list_run+') run '+str(nb_ms_to_run)+ ' MS with differents parameters', context, True)
else:
  MSA_API.task_success('DONE in '+str(exec_sec)+' sec: Get Status for ' + ' and '.join(devices.keys()) + ' '+ message + ' devices ('+MS_list_run+'), run '+str(nb_ms_to_run)+ ' MS with differents parameters', context, True)



