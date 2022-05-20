import json
import re
import os.path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk.conf_profile import ConfProfile
from pathlib import Path
from datetime import datetime
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()
dev_var.add('rollback_generate_file')
context = Variables.task_call(dev_var)

push_to_device = context['push_to_device']
context['push_to_device'] = 'false'  #reset values

timeout = 3600

#get device_id from context
device_id_full = context['destination_device_id']
device_id = device_id_full[3:]
# instantiate device object
obmf  = Order(device_id=device_id)

#Get the list of MS to RUN from 
#read import_WF_parameters_into_MS.txt file
wf_path = os.path.dirname(__file__)
if not context.get('rollBack_config_file'):
  context['rollBack_config_file'] = 'Configuration/rollback_config.txt'
file =  wf_path+'/../'+context['rollBack_config_file']   # rollBack_config.txt
MS_To_Run = []
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  import_liste = file1.read()
  file1.close()
  data_list = import_liste.split('\n')
  data_list = [i for i in data_list if i] #remove empty element
  MS_To_Run = []

  if data_list:
    for line in data_list:
      if (not line.startswith('#')) and line.strip():
        MS_To_Run.append(line)       
else:
  MSA_API.task_error('Can not open file "' + file + '"', context, True)


command = 'DELETE'
 

MS_source_path = context['MS_source_path']
MS_rollback =[]

####### GEt the list of MS attached to the destination device:
# Get deployment settings ID for the device.
deployment_settings_id = obmf.command_get_deployment_settings_id()
context['destination_deployment_settings_id'] = deployment_settings_id

if not deployment_settings_id:
  MSA_API.task_error('There is no deployement setting for the Cisco device '+context['destination_device_id'], context, True)

#Get all microservices attached to this deployment setting.
confprofile  = ConfProfile(deployment_settings_id)
all_ms_attached = confprofile.read()
all_ms_attached = json.loads(all_ms_attached)
MS_To_Run_destination=[]
MS_To_Run_destination_order = {}
all_order = {}
if all_ms_attached.get("microserviceUris"):
  all_ms_attached = all_ms_attached["microserviceUris"] 
  #context[ 'MS_attached destination device_id' + device_id + ' : '] = all_ms_attached

  # all_ms_attached = {        "CommandDefinition/LINUX/CISCO_IOS_XR_emulation/address_family.xml": {"name": "address_family","groups": ["EMULATION","CISCO", "IOS"],"order": 0,"importRank": 10},
  
  if all_ms_attached:
    # We should sort by the value 'importRank', but we can have many MS with samed importRank values
    for full_ms, MS in all_ms_attached.items():
      if Path(full_ms).stem:
        importRank = MS['importRank']
        if MS_To_Run_destination_order.get(importRank):
          MS_To_Run_destination_order[importRank].append(Path(full_ms).stem)
        else:
          MS_To_Run_destination_order[importRank] = []
          MS_To_Run_destination_order[importRank].append(Path(full_ms).stem)
      
    if MS_To_Run_destination_order:
      orderlist = sorted(MS_To_Run_destination_order.keys())
      for importRank in orderlist:
        if  MS_To_Run_destination_order.get(importRank):
          for  val in MS_To_Run_destination_order[importRank]:
            MS_To_Run_destination.append(val)   
            
context['MS_To_Run_destination_RollBack']  = MS_To_Run_destination

ms_not_attached_destination_device = []
full_message = '!############# ROLLBACK PART ############# \n'

if (push_to_device == 'true' or push_to_device == True):
  mode = 2  #mode=2 : Apply to device and in DB
else:
  mode = 0  #mode=0 : not applied to device, no added to db
          
if MS_To_Run:
  for MS in MS_To_Run:
    if MS in  MS_To_Run_destination:
      config = json.loads(context.get( MS + '_values_serialized')) 
      if config:
        params = dict()
        params[MS] = config
         #context[MS + '_rollback__export_params'] = params
     
        obmf.command_call(command, mode, params, timeout)  
        response = json.loads(obmf.content)
        #context[ MS + '_rollback_generate_response'] = response
        # bgp_vrf_generate_response": {
          # "entity": {
              # "commandId": 0,
              # "status": "OK",
              # "message": "\n!\nip vrf  TRIBUNAL-JUSTICA\n\n#exit\n!\n!\nip vrf  V1038:Bco_Bradesco\n\n#exit\n!\n!\nip vrf  V4815:Sabesp_Intragov\n  rd  \n\n  export map  \n#exit\n!"
          # },
          
        if response.get("entity"):
          if response.get("entity").get("status") == "OK":
           if response.get("entity").get("message"):
            # response =    "message": "\nip vrf  V4815:Sabesp_Intragov\n  description  \n  rd  \n\n    route-target export 10429:11048 \n     route-target import 10429:102 \n     route-target import 10429:11048 \n \n\n  export map  \n"
            message =  response.get("entity").get("message") 
            message = re.sub('\s+\n', '\n', message, flags=re.UNICODE)  #remove blank lines
            message = re.sub('  \s+', '  ', message, flags=re.UNICODE)      #remove more than 2 blank space, but  \s+ remove also newline
  
            full_message = full_message + '\n\n!############# from MS ' + MS+  ' ############# '  + message

            MS_rollback.append(MS)
            

          else:
            MSA_API.task_error('On device '+device_id_full+' Can not run '+command+' on MS: '+ MS + ', response='+ str(response) , context, True)
        else: 
          if 'wo_newparams' in response:
            MSA_API.task_error('On device '+device_id_full+' Can not run '+command+' on MS: '+ MS + ', response='+ str(response.get('wo_newparams')), context, True)
          else:
             MSA_API.task_error('On device '+device_id_full+' Can not run '+command+' on MS: '+ MS + ', response='+ str(response) , context, True)
    else:
      ms_not_attached_destination_device.append(MS)

#Create the global rollback generate file :
now = datetime.now() # current date and time
day = now.strftime("%m-%d-%Y-%Hh%M")
file =   DIRECTORY + "/RollBack_generate_" + context['SERVICEINSTANCEID'] + "_"  + day + '.txt'
context['rollback_generate_file'] = file
f = open(file, "w")
f.write(full_message)
f.close()


if ms_not_attached_destination_device:
  if (push_to_device == 'true' or push_to_device == True):
    MSA_API.task_success('Applied to device, Warning , some MS ('+';'.join(ms_not_attached_destination_device)+') was not found for destination device :'+context['destination_device_id']+', other MS run delete part successfully ('+';'.join(MS_rollback)+') cf '+file, context, True)
  else:
    MSA_API.task_success('SIMULATED Warning , some MS ('+';'.join(ms_not_attached_destination_device)+') was not found for destination device :'+context['destination_device_id']+', other MS may run delete part successfully ('+';'.join(MS_rollback)+') cf '+file, context, True)

else:
  if (push_to_device == 'true' or push_to_device == True):
    MSA_API.task_success('Applied to device, Good, all MS ('+', '.join(MS_To_Run)+') run delete part for DeviceId:'+context['destination_device_id']+' successfully cf '+file , context, True)
  else:
    MSA_API.task_success('SIMULATED, Good, all MS ('+', '.join(MS_To_Run)+') run delete part for DeviceId:'+context['destination_device_id']+' successfully, new rollback generated file : '+file , context, True)
