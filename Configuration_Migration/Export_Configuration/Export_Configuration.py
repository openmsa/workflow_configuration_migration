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
 
context = Variables.task_call(dev_var)

timeout = 600

#get device_id from context
device_id = context['destination_device_id'][3:]
# instantiate device object
obmf  = Order(device_id=device_id)


MS_destination_path = context['MS_destination_path']
MS_list        = context['MS_list']  
MS_list        = MS_list.replace(' ;',';')     
MS_list        = MS_list.replace('; ',';')     
command = 'CREATE'
 
if MS_list:
  for MS in  MS_list.split(';'):
    #mservice = ["CommandDefinition/LINUX/CISCO_IOS_emulation/interface.xml"]
    context.update(destination_device_id = device_id)
    
    config = context.get( MS + '_values')
    #config['object_id']= MS   #add mandatory field object_id, put only one default value
    params = dict()
    params[MS] = config
    context[MS + '_export_params'] = params
    
    obmf.command_execute(command, params, timeout) #execute the MS ADD static route operation
    
    #object_name = MS
    #params = dict()
    #params[object_name] = "0"
    #Import the given device microservice from the device, the MS values in the UI will be not updated
    #obmf.command_call(command, 0, params)
 
    response = json.loads(obmf.content)
    context[ MS + '_export_response'] = response
    
    if response.get('wo_status') == constants.FAILED:
      if 'wo_newparams' in response:
        MSA_API.task_error('Failure details: ' + response.get('wo_newparams'), context, True)
      else:
        MSA_API.task_error('Failure details: ' + str(response) , context, True)
    
MSA_API.task_success('Good, all MS ('+MS_list+') imported for DeviceId:'+context['destination_device_id'], context, True)



