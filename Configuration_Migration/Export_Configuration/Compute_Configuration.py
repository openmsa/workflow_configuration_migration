import json
import copy
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()

dev_var.add('customer_id', var_type='String')
dev_var.add('MS_list', var_type='String')
dev_var.add('source_interfaces_name', var_type='String')
dev_var.add('destination_interfaces_name', var_type='String')

context = Variables.task_call(dev_var)


#get device_id from context
device_id = context['destination_device_id'][3:]

#Change the interface_name
source_interfaces_name      = context['source_interfaces_name']
destination_interfaces_name = context['destination_interfaces_name']
context['interface_values_orig'] = copy.deepcopy(context['interface_values'])
interfaces_newvalues = context['interface_values']

if source_interfaces_name and destination_interfaces_name:
  source_interfaces_name_list = source_interfaces_name.split(';')
  destination_interfaces_name_list = destination_interfaces_name.split(';')
  if len(source_interfaces_name_list) != len(destination_interfaces_name_list):
    MSA_API.task_error('Error, the length of old interfaces names and nex interfaces name are differentes (old=('+source_interfaces_name+'), new=('+destination_interfaces_name+')', context, True)
  for i in range(len(source_interfaces_name_list)):
    old_interface_name = source_interfaces_name_list[i]
    new_interface_name = destination_interfaces_name_list[i]
    '''    "interface_values": {
        "Multilink45": {
            "addresses": {
                "0": {
                    "ipv4_address": "186.239.12.61",
                    "ipv4_mask": "255.255.255.252"
                }
            },
            "int_description": "By VPNSC: Job Id# = 178482 (Sabesp_SAO_PAULO_SP_582841)",
            "object_id": "Multilink45",
            "ppp": {
    '''
    if interfaces_newvalues.get(old_interface_name):
      if interfaces_newvalues.get(new_interface_name):
        MSA_API.task_error('Error, interface name "'+new_interface_name+'" already exist on the device', context, True)
      interfaces_newvalues[new_interface_name] = interfaces_newvalues[old_interface_name]
      if (interfaces_newvalues[new_interface_name].get("object_id")):
        interfaces_newvalues[new_interface_name]["object_id"] = new_interface_name
      del interfaces_newvalues[old_interface_name]  


context['interface_values'] = interfaces_newvalues 


MSA_API.task_success('Good, update the interfaces names', context, True)



