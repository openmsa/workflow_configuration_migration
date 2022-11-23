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

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]

timeout = 10800

device_id_full = context['source_device_id_full']
device_id      = device_id_full[3:]

# instantiate device object
obmf  = Order(device_id=device_id)

context['customer_id_instance_id'] =  context['customer_id'] + '_#' +context['SERVICEINSTANCEID']

#read import_WF_parameters_into_MS.txt file to get the list of MS to import:
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../'+context['get_device_configuration_file']   # Configuration/get_device_configuration.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  import_liste = file1.read()
  file1.close()
  data_list = import_liste.split('\n')
  data_list = [i for i in data_list if i] #remove empty element
else:
  msg = 'Can not open file "' + file + '"'
  create_event(device_id_full, "1", "MIGRATION", "IMPORT",  subtenant_ref, subtenant_id, msg)
  MSA_API.task_error(msg, context, True)
  data_list = ''    
  
MS_wanted=[]
if data_list:
  MS_to_import={}
  for line in data_list:
    if (not line.startswith('#')) and line.strip():
      list = line.split('|') 
      #MS|Importrank(integer, 0=first)      
      if len(list) > 1:
        MS         = list[0]
        importrank = list[1]
        if not MS_to_import.get(importrank):
          MS_to_import[importrank] = []
        MS_to_import[importrank].append(MS)
        MS_wanted.append(MS) 
  
# Get deployment settings ID for the device.
deployment_settings_id = obmf.command_get_deployment_settings_id()
context['source_deployment_settings_id_'+device_id_full] = deployment_settings_id

#Get all microservices attached to this deployment setting.
confprofile  = ConfProfile(deployment_settings_id)
all_ms_attached = confprofile.read()
all_ms_attached = json.loads(all_ms_attached)
#context['MS_attached source device_id' + device_id + ' : '] = all_ms_attached
if all_ms_attached.get("microserviceUris"):
  all_ms_attached_uris = all_ms_attached["microserviceUris"] 
#all_ms_attached = {"id" : 44, ..."microserviceUris" : { "CommandDefinition/LINUX/CISCO_IOS_emu  },  "CommandDefinition/LINUX/CISCO_IOS_emulation/bgp_vrf.xml" : {  "name" : "bgp_vrf",   "groups" : [ "EMULATION", "CISCO", "IOS" ].....
else:
  all_ms_attached_uris={}   

MS_list     = []
MS_FullPath = {}   
if all_ms_attached_uris:
  for full_ms, MS in all_ms_attached_uris.items():
    if Path(full_ms).stem:
      MS_list.append(Path(full_ms).stem)    # Path(full_ms).stem = MS filename without extension
      MS_FullPath[Path(full_ms).stem] = full_ms
   
if MS_list:
  MS_list_string             = ';'.join(MS_list)  
  context['MS_list']  = MS_list_string
else:
  MS_list = ''
    
#Check if missing MS in the deploiement setting :
missing_MS_in_deployment_setting = []
for MS in MS_wanted:
  if not MS in MS_list:
    missing_MS_in_deployment_setting.append(MS)
  
if missing_MS_in_deployment_setting:  
  msg = 'Some MS ('+', '.join(missing_MS_in_deployment_setting) + ') are missing in the deployment settings "'+all_ms_attached['name']+' (id='+str(all_ms_attached['id'])+')" for device '+ device_id_full +', please add theim'
  create_event(device_id_full, "5", "MIGRATION", "SYNCHRONIZE", subtenant_ref, subtenant_id, msg)
  MSA_API.task_error(msg, context, True)
  
# The import is order by importrank of the MS. 
# So we import all MS at the same times which have the same importrank. 
responses = []
for importrank in sorted(MS_to_import):
  mservice_uris = []
  for MS in MS_to_import[importrank]:
    mservice_uris.append(MS_FullPath[MS]) 
  obmf.command_synchronizeOneOrMoreObjectsFromDevice(mservice_uris, timeout) #synchronize given MS to get new values (import+update DB) 
  response = json.loads(obmf.content)
  #context['response_rank_'+importrank] = response
  if (isinstance(response, typing.List) and response[0].get("status") and response[0]["status"] == "OK" and response[0].get("message")):
    response =  response[0]["message"]
    responses.append(response)
  else:
    msg = 'Can not synchronise device '+ device_id_full + ' : '+ str(response)
    create_event(device_id_full, "1", "MIGRATION", "SYNCHRONIZE", subtenant_ref, subtenant_id, msg)
    MSA_API.task_error(msg, context, True)


create_event(device_id_full, "5", "MIGRATION", "SYNCHRONIZE", subtenant_ref, subtenant_id, "IMPORT:END:"+device_id_full)


if isinstance(responses, typing.List): 
  #responses contains only MS which contains some datas, we don't get attached MS without datas
  for response in responses:
    response_message = json.loads(response)  #convert into json array
    for MS in response_message:
      if response_message.get(MS):
        context[ MS + '_values_serialized'] = json.dumps(response_message.get(MS))
      else:
        context[ MS + '_values_serialized'] = json.dumps(response_message)
            

msg = 'DONE: all MS attached to the managed entity: '+ device_id_full + ' imported ('+', '.join(MS_wanted) +')'
create_event(device_id_full, "5", "MIGRATION", "SYNCHRONIZE", subtenant_ref, subtenant_id, msg)
MSA_API.task_success(msg, context, True)



