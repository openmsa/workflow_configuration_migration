import json
import copy
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime

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
if context.get('interface_values'):
  context['interface_values_orig'] = copy.deepcopy(context['interface_values'])
  interfaces_newvalues = context['interface_values']

  #source_interfaces_name      = source_interfaces_name.replace('.','_')  # replace '.' with '_'
  #destination_interfaces_name = destination_interfaces_name.replace('.','_')  # replace '.' with '_'
  #context['source_interfaces_name_corrected'] = source_interfaces_name 

  if source_interfaces_name and destination_interfaces_name:
    source_interfaces_name_list = source_interfaces_name.split(';')
    destination_interfaces_name_list = destination_interfaces_name.split(';')
    if len(source_interfaces_name_list) != len(destination_interfaces_name_list):
      MSA_API.task_error('Error, the length of old interfaces names and nex interfaces name are differentes (old=('+source_interfaces_name+'), new=('+destination_interfaces_name+')', context, True)
    for i in range(len(source_interfaces_name_list)):
      old_interface_name = source_interfaces_name_list[i]
      new_interface_name = destination_interfaces_name_list[i]
      old_interface_name_ob      = old_interface_name.replace('.','_')  # replace '.' with '_'
      new_interface_name_ob      = new_interface_name.replace('.','_')  # replace '.' with '_'

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
      if interfaces_newvalues.get(old_interface_name_ob):
        if interfaces_newvalues.get(new_interface_name_ob):
          MSA_API.task_error('Error, interface name "'+new_interface_name_ob+'" already exist on the device', context, True)
        interfaces_newvalues[new_interface_name_ob] = interfaces_newvalues[old_interface_name_ob]
        if (interfaces_newvalues[new_interface_name_ob].get("object_id")):
          interfaces_newvalues[new_interface_name_ob]["object_id"] = new_interface_name
        del interfaces_newvalues[old_interface_name_ob]  
  
  context['interface_values'] = interfaces_newvalues 


########### ADD LINK #############
MS_list        = context['MS_list']  
MS_list        = MS_list.replace(' ;',';')     
MS_list        = MS_list.replace('; ',';')     

now = datetime.now() # current date and time
day = now.strftime("%m-%d-%Y-%H:%m")
    
if MS_list:
  for MS in  MS_list.split(';'):
    if MS:

      # Add the download file link for each values
      filelinks={}
      config = context.get( MS + '_values')
      for key in config:
        #link = "/opt/fmc_repository/Datafiles/TEST/" + MS + '_' + key +'_' + day + '.html'
        link = "/opt/fmc_repository/Datafiles/TEST/" + MS + '_'  + day + '.html'
        link_orig = "/opt/fmc_repository/Datafiles/TEST/" + MS + '_'  + day + '_orig.html'
        config[key]['link'] = link
        filelinks[key]      = link
        context[MS + '_link'] = link
        context[MS + '_link_orig'] = link_orig
      context[MS + '_values'] = config
    


MSA_API.task_success('Good, update the interfaces names', context, True)



