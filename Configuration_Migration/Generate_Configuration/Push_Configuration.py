import json
import re
import os.path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk.conf_profile import ConfProfile
from pathlib import Path
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()

context = Variables.task_call(dev_var)

if not context.get('push_to_device'):
  context['push_to_device'] = 'false'

push_to_device = context['push_to_device']


#check if the folder  DIRECTORY exist, else create it
if not os.path.isdir(DIRECTORY):
 os.mkdir(DIRECTORY)
 
timeout = 3600

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]
#get device_id from context
device_id_full = context['destination_device_id']
device_id = device_id_full[3:]
# instantiate device object
obmf  = Order(device_id=device_id)

if (context['real_device_source'] == 'false' or context['real_device_source'] == False) and (context['push_to_device']== 'true' or context['push_to_device']== True):
  msg = 'ERROR: Before to push the configuration to real device '+device_id_full+', you should Import first the configuration from real device '+context['source_device_id']
  create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG",  subtenant_ref, subtenant_id, msg)
  context['push_to_device'] = 'false'        #reset value
  MSA_API.task_error(msg, context, True)

context['push_to_device'] = 'false'        #reset value

MS_list        = context['MS_list']  
MS_list        = MS_list.replace(' ;',';')     
MS_list        = MS_list.replace('; ',';')     
command = 'CREATE'
 
links =[]
MS_source_path = context['MS_source_path']
MS_imported =[]

####### GEt the list of MS attached to the destination device:
# Get deployment settings ID for the device.
deployment_settings_id = obmf.command_get_deployment_settings_id()
context['destination_deployment_settings_id'] = deployment_settings_id

if not deployment_settings_id:
  msg = 'ERROR: There is no deployement setting for the managed entity '+device_id_full
  create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG",  subtenant_ref, subtenant_id, msg)
  MSA_API.task_error(msg, context, True)
  
#Get all microservices attached to this deployment setting.
confprofile  = ConfProfile(deployment_settings_id)
all_ms_attached = confprofile.read()
all_ms_attached = json.loads(all_ms_attached)
MS_list_destination=[]
MS_list_destination_order = {}
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
        if MS_list_destination_order.get(importRank):
          MS_list_destination_order[importRank].append(Path(full_ms).stem)
        else:
          MS_list_destination_order[importRank] = []
          MS_list_destination_order[importRank].append(Path(full_ms).stem)
      
    if MS_list_destination_order:
      orderlist = sorted(MS_list_destination_order.keys())
      for importRank in orderlist:
        if  MS_list_destination_order.get(importRank):
          for  val in MS_list_destination_order[importRank]:
            MS_list_destination.append(val)   
            
context['MS_list_destination']  = MS_list_destination

ms_not_attached_destination_device = []
full_message = ''

if (push_to_device == 'true' or push_to_device == True):
  mode = 2  #mode=2 : Apply to device and in DB
else:
  mode = 1  #mode=1 : Apply only in hte DB, not applied on the device
          
if MS_list:
  for MS in  MS_list_destination:
    if MS and MS in MS_list.split(';'):
      if context.get( MS + '_values_serialized'):
        config = json.loads(context.get( MS + '_values_serialized')) 
        params = dict()
        params[MS] = config
        #context[MS + '_export_params'] = params
          
        obmf.command_call(command, mode, params, timeout) 
   
        response = json.loads(obmf.content)
        #context[ MS + '_generate_response'] = response
        # bgp_vrf_generate_response": {
          # "entity": {
              # "commandId": 0,
              # "status": "OK",
              # "message": "\n!\nip vrf  TRIBUNAL-JUSTICA\n\n#exit\n!\n!\nip vrf  V1038:Bco_Bradesco\n\n#exit\n!\n!\nip vrf  V4815:Sabesp_Intragov\n  rd  \n\n  export map  \n#exit\n!"
          # },
          
        if response.get("entity"):
          if response.get("entity").get("status") and response["entity"]["status"] == "OK":
           if response.get("entity").get("message"):
            # response =    "message": "\nip vrf  V4815:Sabesp_Intragov\n  description  \n  rd  \n\n    route-target export 10429:11048 \n     route-target import 10429:102 \n     route-target import 10429:11048 \n \n\n  export map  \n"
            message =  response.get("entity").get("message") 
            file_link = context[MS + '_link']
            message = re.sub('\s+\n', '\n', message, flags=re.UNICODE)  #remove blank lines
            message = re.sub('  \s+', '  ', message, flags=re.UNICODE)      #remove more than 2 blank space, but  \s+ remove also newline
            #message = '<pre> \n' + message + '\n </pre>'
            f = open(file_link, "w")
            f.write(message)
            f.close()
            full_message = full_message + '\n\n!############# from MS ' + MS+  ' ############# \n'  + message
            link={}
            link['MicroService'] = MS
            link['file_link']    = file_link
            links.append(link)
            MS_imported.append(MS)
            
            #Add original file link:
            source_MS_file = ''
            if MS_source_path:
              MS_file = '/opt/fmc_repository/'+ MS_source_path +'/' + MS + '.xml'
              if os.path.isfile(MS_file):
                file1 = open(MS_file, "r")
                # read file content
                readfile = file1.read()
                file1.close()
                #find <operation><![CDATA[cat /config/cisco_ios/sample-config.ios.V4815.txt]]></operation>
                match = re.search('cat (.+)]]', readfile)

                if match:
                  source_MS_file = match.group(1)
                  context['source_MS_file'] = source_MS_file
                  if '/opt/fmc_repository/Datafiles/' not in source_MS_file:
                    source_MS_file = '/opt/fmc_repository/Datafiles/' + source_MS_file
                  
                  if os.path.isfile(source_MS_file):
                    file1 = open(source_MS_file, "r")
                    # read file content
                    readfile = file1.read()
                    file1.close()
                    f = open(context[MS + '_link_orig'], "w")
                    f.write( '<pre> \n' + readfile + '\n </pre>')
                    f.close()
                    link={}
                    link['MicroService'] = MS + '_original'
                    link['file_link']    = context[MS + '_link_orig']
                    links.append(link)
                   
                
            #Add MS import Skip result link:
            MS_file = DIRECTORY + '/' + MS + '.log'
            link={}
            link['MicroService'] = MS + '_Import_parse'
            link['file_link']    = MS_file       
            links.append(link)

          else:
            msg = 'ERROR: Cannot run CREATE on microservice: '+ MS + ', response='+ str(response)
            create_event(device_id_full, "1",  "MIGRATION", "GEN_CONFIG",  subtenant_ref, subtenant_id, msg)
            MSA_API.task_error(msg , context, True)
        else: 
          if 'wo_newparams' in response:
            msg = 'ERROR: Cannot run CREATE on microservice: '+ MS + ', response='+ str(response.get('wo_newparams'))
            create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG", subtenant_ref, subtenant_id, msg)
            MSA_API.task_error(msg, context, True)
          else:
            msg = 'ERROR: Cannot run CREATE on microservice: '+ MS + ', response='+ str(response)
            create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG", subtenant_ref, subtenant_id, msg)
            MSA_API.task_error(msg , context, True)
    else:
      ms_not_attached_destination_device.append(MS)
    
context['link'] = links 

#Create the global config file :

f = open(context['generate_file'], "w")
f.write(full_message)
f.close()

if ms_not_attached_destination_device:
  if (push_to_device == 'true' or push_to_device == True):
    context['pushed_to_destination_device'] = 'true'    
    MSA_API.task_success('Applied to device, WARNING, some microservices ('+';'.join(ms_not_attached_destination_device)+') not found for destination device :'+device_id_full+', other microservice imported successfully ('+';'.join(MS_imported)+')', context, True)
  else:
    MSA_API.task_success('SIMULATED, WARNING , some microservices ('+';'.join(ms_not_attached_destination_device)+') not found for destination device :'+device_id_full+', other microservice imported successfully ('+';'.join(MS_imported)+')', context, True)
else:
  if (push_to_device == 'true' or push_to_device == True):
    context['pushed_to_destination_device'] = 'true'    
    MSA_API.task_success('Applied to device DONE, microservices ('+MS_list+') imported for managed entity: '+device_id_full, context, True)
  else:
    MSA_API.task_success('SIMULATED, DONE, microservices ('+MS_list+') imported for managed entity: '+device_id_full, context, True)
  



