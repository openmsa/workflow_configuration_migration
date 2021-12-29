import json
import re
import os.path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk.conf_profile import ConfProfile

dev_var = Variables()
dev_var.add('source_interfaces_name' )
dev_var.add('destination_interfaces_name')
dev_var.add('customer_id')
 
context = Variables.task_call(dev_var)

timeout = 600

#get device_id from context
device_id = context['destination_device_id'][3:]
# instantiate device object
obmf  = Order(device_id=device_id)


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

#Get all microservices attached to this deployment setting.
confprofile  = ConfProfile(deployment_settings_id)
all_ms_attached = confprofile.read()
all_ms_attached = json.loads(all_ms_attached)
MS_list_destination=[]
if all_ms_attached.get("microserviceUris"):
  all_ms_attached = all_ms_attached["microserviceUris"] 
  context[ 'MS_attached destination device_id' + device_id + ' : '] = all_ms_attached
  if all_ms_attached:
    for full_ms, MS in all_ms_attached.items():
      if Path(full_ms).stem:
        MS_list_destination.append(Path(full_ms).stem)   #MS filename without extension
        
context['MS_list_destination']  = MS_list_destination

ms_not_attached_destination_device = []

if MS_list:
  for MS in  MS_list.split(';'):
    if MS and MS in MS_list_destination:
      config = context.get( MS + '_values') 
      if config:
        params = dict()
        params[MS] = config
        context[MS + '_export_params'] = params
        #obmf.command_execute(command, params, timeout) #execute the MS ADD static route operation
        obmf.command_call(command, 1, params, timeout)  #mode=1 :  Apply to base only (create new element in the MSA DB, it will not run any commands on device)
   
        response = json.loads(obmf.content)
        context[ MS + '_generate_response'] = response
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
            context[ MS + '_generate_response_message'] = message
            file_link = context[MS + '_link']
            message = re.sub(r'\n\s*\n', '\n', message)  #remove blank lines
            #message = '<pre> \n' + message + '\n </pre>'
            f = open(file_link, "w")
            f.write(message)
            f.close()
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
            MS_file = '/opt/fmc_repository/Datafiles/Import_MS_Result/' + MS + '.log'
            link={}
            link['MicroService'] = MS + '_Import_parse'
            link['file_link']    = MS_file       
            links.append(link)

          else:
            MSA_API.task_error('Can not run create on MS: '+ MS + ', response='+ str(response) , context, True)
        else: 
          if 'wo_newparams' in response:
            MSA_API.task_error('Can not run create on MS: '+ MS + ', response='+ str(response.get('wo_newparams')), context, True)
          else:
             MSA_API.task_error('Can not run create on MS: '+ MS + ', response='+ str(response) , context, True)
    else:
      ms_not_attached_destination_device.append(MS)
    
context['link'] = links 

if ms_not_attached_destination_device:
  MSA_API.task_success('Warning , some MS ('+';'.join(ms_not_attached_destination_device)+') was not found for destination device :'+context['destination_device_id']+', other MS imported successfully ('+';'.join(MS_imported)+')', context, True)
else:
  MSA_API.task_success('Good, all MS ('+MS_list+') imported for DeviceId:'+context['destination_device_id'], context, True)



