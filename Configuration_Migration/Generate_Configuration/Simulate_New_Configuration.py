import json
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()
#dev_var.add('source_device_id' )
dev_var.add('source_interfaces_name' )
#dev_var.add('destination_device_id')
dev_var.add('destination_interfaces_name')
dev_var.add('customer_id')
dev_var.add('MS_list')
 
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
#command = 'CREATE'
command = 'READ'
 
if MS_list:
  for MS in  MS_list.split(';'):
    #mservice = ["CommandDefinition/LINUX/CISCO_IOS_emulation/interface.xml"]
    
    config = context.get( MS + '_values')
    ''' config = {
        "V4815:Sabesp_Intragov": {
            "description": "Description V4815:Sabesp_Intragov ",
            "object_id": "V4815:Sabesp_Intragov",
            "rd": "10429:4765",
            "route_map": "grey_mgmt_vpn_Telefonica_Empresas_V4815:Sabesp_Intragov",
            "route_target": {
                "0": {
                    "rt": "export 10429:11048"
                },
                "1": {
                    "rt": "import 10429:102"
                },
                "2": {
                    "rt": "import 10429:11048"
                }
            }
        }
    },
    '''

    params = dict()
    params[MS] = config
    context[MS + '_simulate_params'] = params
    
    obmf.command_execute(command, params, timeout) #execute the MS ADD static route operation
    
    #object_name = MS
    #params = dict()
    #params[object_name] = "0"
    #Import the given device microservice from the device, the MS values in the UI will be not updated
    #obmf.command_call(command, 0, params)
 
    response = json.loads(obmf.content)
    context[ MS + '_simulate_response'] = response
    if response.get("status") == "OK":
      if response.get("message"):
         # response =    "message": "\nip vrf  V4815:Sabesp_Intragov\n  description  \n  rd  \n\n    route-target export 10429:11048 \n     route-target import 10429:102 \n     route-target import 10429:11048 \n \n\n  export map  \n"
         message =  response.get("message") 
         context[ MS + '_simulate_response_message'] = message
         link = context[MS + '_link']
         message = '<pre> \n' + message + '\n </pre>'
         f = open(link, "w")
         f.write(message)
         f.close()

    else: 
      if 'wo_newparams' in response:
        MSA_API.task_error('Failure details: ' + response.get('wo_newparams'), context, True)
      else:
        MSA_API.task_error('Failure details: ' + str(response) , context, True)
    

    
    
    
MSA_API.task_success('Good, all MS ('+MS_list+') imported for DeviceId:'+context['destination_device_id'], context, True)



