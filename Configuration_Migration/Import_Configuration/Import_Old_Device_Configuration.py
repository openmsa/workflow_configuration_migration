import json
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()
dev_var.add('source_device_id', var_type='Device')
dev_var.add('source_interfaces_name', var_type='String')
dev_var.add('destination_device_id', var_type='Device')
dev_var.add('destination_interfaces_name', var_type='String')
dev_var.add('customer_id', var_type='String')
dev_var.add('MS_list', var_type='String')
dev_var.add('link.0.MicroService', var_type='String')
dev_var.add('link.0.file_link', var_type='Link')

context = Variables.task_call(dev_var)

timeout = 600

#get device_id from context
device_id = context['source_device_id'][3:]
context.update(source_device_id = device_id)

# instantiate device object
obmf  = Order(device_id=device_id)
 
MS_source_path = context['MS_source_path']
MS_list        = context['MS_list']  
MS_list        = MS_list.replace(' ;',';')     
MS_list        = MS_list.replace('; ',';')     
     
if MS_list:
  for MS in  MS_list.split(';'):
    #mservice = ["CommandDefinition/LINUX/CISCO_IOS_emulation/interface.xml"]
    mservice = [MS_source_path+'/' + MS + ".xml"]
    context.update(mservice = mservice)
    #Synchronize (read from Device + update MSA-DB) only 1 MS each time:
    obmf.command_synchronizeOneOrMoreObjectsFromDevice(mservice, timeout)
    response = json.loads(obmf.content)
    response = response[0]  # synchronyse only 1 ms, so get only first output
    context[ MS + '_values'] = response
    
    if response.get('wo_status') == constants.FAILED or response.get('status') != 'OK':

      if 'wo_newparams' in response:
        MSA_API.task_error('Failure details: ' + response.get('wo_newparams'), context, True)
      else:
        MSA_API.task_error('Failure details: ' + str(response) , context, True)

    #context['obmf_command_synchronize_' + MS] = response
    if response.get('message'):
      # message": "{\"ip_vrf\":{\"V4815:Sabesp_Intragov\":{\"object_id\":\"V4815:Sabesp_Intragov\",\"rd\":\"10429:4765\",\"route_map\":\"grey_mgmt_vpn_Telefonica_Empresas_V4815:Sabesp_Intragov\",\"route_target\":{\"0\":{\"rt\":\"export 10429:11048\"},\"1\":{\"rt\":\"import 10429:102\"},\"2\":{\"rt\":\"import 10429:11048\"}}}}}"
      response_message = json.loads(response.get('message'))  #convert into json array
      if response_message.get(MS):
        context[ MS + '_values'] = response_message.get(MS)
      else:
        context[ MS + '_values'] = response_message
    
    
MSA_API.task_success('Good, all MS ('+MS_list+') imported for DeviceId:'+context['source_device_id'], context, True)



