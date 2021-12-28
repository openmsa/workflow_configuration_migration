import json
import copy
import typing
import os.path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime

dev_var = Variables()

dev_var.add('customer_id', var_type='String')
dev_var.add('source_interfaces_name', var_type='String')
dev_var.add('destination_interfaces_name', var_type='String')
dev_var.add('data_conversion', var_type='String')

context = Variables.task_call(dev_var)

#########################################################
# Function: Parse all MS values recursivly and change the value (by reference) if needed 
def  data_conversion_recursif(ms_newvalues, fields, convert_condition, convert_pattern_source, convert_pattern_destination):
   if isinstance(fields, typing.List) and fields:
     field = fields[0]
     fields.pop(0)
   else:
     field = fields  #string
   if field:
     if isinstance(ms_newvalues, dict):
       for  key, value1 in ms_newvalues.items():
       #for key in ms_newvalues:
         if isinstance(value1, dict):
           if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               data_conversion_recursif(value1[field], copy.deepcopy(fields), convert_condition, convert_pattern_source, convert_pattern_destination) 
             else:
               if value :
                 source=''
                 # CAN NOT used try.... because it will not parse all values in ms_newvalues (try will used only first value), so we used one convert_condition
                 if eval(convert_condition):
                   source      = eval(convert_pattern_source)
                   destination = eval(convert_pattern_destination)
       
                   if source:
                     context['result_source_'+value]      = source
                     context['result_destination_'+value] = destination
                     ms_newvalues[key][field] = value.replace(source,destination)
               
   return 'ok'
   
   
   
#get device_id from context
device_id = context['destination_device_id'][3:]

#########################################################
source_interfaces_name      = context['source_interfaces_name']
destination_interfaces_name = context['destination_interfaces_name']

#CHANGE THE INTERFACE NAME in INTERFACE MS
#if context.get('interface_values') and not context.get('interface_values_orig'):
#  context['interface_values_orig'] = copy.deepcopy(context['interface_values'])

if context.get('interface_values'):
  interfaces_newvalues = context['interface_values']
  if source_interfaces_name and destination_interfaces_name:
    source_interfaces_name_list = source_interfaces_name.split(';')
    destination_interfaces_name_list = destination_interfaces_name.split(';')
    if len(source_interfaces_name_list) != len(destination_interfaces_name_list):
      MSA_API.task_error('Error, the length of old interfaces names and new interfaces name are differentes (old=('+source_interfaces_name+'), new=('+destination_interfaces_name+')', context, True)
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

#CHANGE THE INTERFACE NAME in IP_ROUTE MS
#if context.get('ip_route_values') and not context.get('ip_route_values_orig'):
#  context['ip_route_values_orig'] = copy.deepcopy(context['ip_route_values'])
if context.get('ip_route_values'):
  ip_routes_newvalues = context['ip_route_values']
  if source_interfaces_name and destination_interfaces_name:
    source_interfaces_name_list = source_interfaces_name.split(';')
    destination_interfaces_name_list = destination_interfaces_name.split(';')
    if len(source_interfaces_name_list) != len(destination_interfaces_name_list):
      MSA_API.task_error('Error, the length of old interfaces names and new interfaces name are differentes (old=('+source_interfaces_name+'), new=('+destination_interfaces_name+')', context, True)
    for i in range(len(source_interfaces_name_list)):
      old_interfaces_name = source_interfaces_name_list[i]
      new_interfaces_name = destination_interfaces_name_list[i]
      ''' ip_route_values": {  "866d05ae2f8822cce90b0d1cf5855c70": {  "vrf_name": "", "ipv4_address": "186.200.4.50",  "interface": "Serial1/1/0.1/3/2/3:0",
      '''
      for key, value in ip_routes_newvalues.items():
        if value.get("interface") and value["interface"] == old_interfaces_name:
          ip_routes_newvalues[key]["interface"] = new_interfaces_name
  
  context['ip_route_values'] = ip_routes_newvalues 
  

########### LOOP ON ALL GIVEN MS #############
MS_list        = context['MS_list']  
MS_list        = MS_list.replace('\s*;\s*',';')     

now = datetime.now() # current date and time
day = now.strftime("%m-%d-%Y-%H:%m")
    
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../' + context['data_conversion_pattern_file']
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  data_conversion = file1.read()
  file1.close()
  data_conversion_list = data_conversion.split('\n')
  data_conversion_list = [i for i in data_conversion_list if i] #remove empty element

else:
  data_conversion_list = ''    
context['data_conversion'] = data_conversion_list


if MS_list:
  for MS in  MS_list.split(';'):
    if MS:

      #########################################################
      # CONVERT SOME MS VALUES FROM THE CONVERTION PATTERN FILE
      if data_conversion_list:
        for line in data_conversion_list:
          if (not line.startswith('#')) and line.strip():
            context['data_conversion_line'] = line+';'
            list = line.split('|')  # MS|Field|Replace Pattern|comment
            if len(list) > 4:
              convert_MS             = list[0]
              convert_field          = list[1]
              convert_condition      = list[2]
              convert_pattern_source = list[3]
              convert_pattern_destination = list[4]
              convert_comment = list[5]

              if convert_MS == MS and context.get(MS+'_values'):
                #if  not context.get(MS+'_values_orig'):
                #  context[MS+'_values_orig'] = copy.deepcopy(context[MS+'_values'])
                ms_newvalues = context[MS+'_values']
                fields = convert_field.split('.0.')
                data_conversion_recursif(ms_newvalues, fields, convert_condition, convert_pattern_source, convert_pattern_destination)
                     
            
      #########################################################
      # ADD THE DOWNLOAD FILE LINK FOR EACH VALUES
      config = context.get( MS + '_values')
      link = "/opt/fmc_repository/Datafiles/TEST/" + MS + '_'  + day + '.txt'
      link_orig = "/opt/fmc_repository/Datafiles/TEST/" + MS + '_'  + day + '_orig.txt'
      
      context[MS + '_link'] = link
      context[MS + '_link_orig'] = link_orig
      context[MS + '_values'] = config
    


MSA_API.task_success('Good, update the interfaces names', context, True)



