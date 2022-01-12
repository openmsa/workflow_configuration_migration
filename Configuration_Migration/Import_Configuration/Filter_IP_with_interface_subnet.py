import json
import copy
import typing
import os.path
import ipaddress
import re
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime

dev_var = Variables()

dev_var.add('customer_id', var_type='String')
dev_var.add('data_filter_ip_file', var_type='String')

context = Variables.task_call(dev_var)
 
 

#########################################################
# Function: Parse all MS values recursivly for the given field
def find_all_ip_in_subnet(interface_name, ipv4_address, ipv4_mask, interfaces_IP_available):
  if ipv4_address and ipv4_mask:
    # convert ipv4 subnet mask to cidr notation 
    len = ipaddress.IPv4Network('0.0.0.0/'+ipv4_mask).prefixlen  #24 
    cidr = ipv4_address+'/'+str(len)
    context['cidr_'+ipv4_address+'/'+ipv4_mask ] =  cidr    # "cidr_": "200.207.251.229/30"
    ips = ipaddress.ip_network(cidr, strict=False)
    ip_list = [str(ip) for ip in ips]    
    for ip in ip_list:
      interfaces_IP_available[str(ip)] = interface_name
    
  return interfaces_IP_available
 
#########################################################
# Function: Parse all MS values recursivly for the given field
def remove_bad_ip_values_recursif(orig_field_name, fields, ms_newvalues, interfaces_IP_available):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
  if field:
    if isinstance(ms_newvalues, dict):
      ms_newvalues2 = copy.deepcopy(ms_newvalues) 
      # We can not remove one element while iterating over it, so itirating on one copy ms_newvalues2
      for  key, value1 in ms_newvalues2.items():
      
        if isinstance(value1, dict):
          if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               remove_bad_ip_values_recursif(orig_field_name, copy.deepcopy(fields), ms_newvalues[key][field], interfaces_IP_available) 
             else:
               if value:
                 match = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", value)
                 if bool(match) and value not in interfaces_IP_available:
                   #ms_newvalues[key][field]  = 'IP_TO_REMOVE_value='+value
                   ms_newvalues.pop(key)  #remove parent value
                 #else: 
                   #ms_newvalues[key][field]  = 'OK TO KEEP_value='+value
                 
  return 'not found'
    
 
MS_list_string        = context['MS_list']  
    
    
#read filter file
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../'  + context['data_filter_ip_file']   # filter_interface_ip.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  data_filter_string = file1.read()
  file1.close()
  ip_data_filter_list = data_filter_string.split('\n')
  ip_data_filter_list = [i for i in ip_data_filter_list if i] #remove empty element
    
else:
  ip_data_filter_list = ''    
  
context['IP_data_filter'] = ip_data_filter_list


#if context.get('interface_values') and not context.get('interface_values_orig'):
#  context['interface_values_orig'] = copy.deepcopy(context['interface_values'])

if not context['enable_filter']:
  MSA_API.task_success('Filter are disabled, no filters applied', context, True)

source_interfaces_name_list = context['source_interfaces_name_list']
interfaces_IP_available = {}
    
if context.get('interface_values'):
  interfaces_values = context['interface_values']
  #interfaces_newvalues: { "Multilink45": { "object_id": "Multilink45", "addresses": { "0": { "ipv4_address": "186.239.124.197", "ipv4_mask": "255.255.255.252" }
  for interface, interface_value in interfaces_values.items():
    if interface in source_interfaces_name_list:
      if interface_value.get("addresses"):
        addresses = interface_value["addresses"]
        for key, address in addresses.items():
          ipv4_address = address["ipv4_address"]
          ipv4_mask    = address["ipv4_mask"]          
          interfaces_IP_available = find_all_ip_in_subnet(interface+'_'+key, ipv4_address, ipv4_mask, interfaces_IP_available)

context['interfaces_IP_available'] = interfaces_IP_available      


context['MS_IP_filter'] = {}

if MS_list_string:
  MS_list = MS_list_string.split('\s*;\s*')
  # FILTER SOME DATA with IP
  if ip_data_filter_list:
    for line in ip_data_filter_list:
      if (not line.startswith('#')) and line.strip():
        context['data_ip_filter_line'] = line
        list = line.split('|')  # #orig_MS_Name|orig_field_name|original_MS_Name|original_field_name
        if len(list) > 1:
          original_MS_Name     = list[0]
          original_field_name  = list[1]
          context['MS_IP_filter'][original_MS_Name] = 1
          if context.get(original_MS_Name+'_values'):
            #if not context.get(original_MS_Name+'_values_orig'):
            #  context[original_MS_Name+'_values_orig'] = copy.deepcopy(context[original_MS_Name+'_values'])
             
            fields = original_field_name.split('.0.')
            remove_bad_ip_values_recursif(original_field_name, fields, context[original_MS_Name+'_values'], interfaces_IP_available);
            

#MSA_API.task_error('TETS33T22  '+ context['data_filter_ip_file'], context, True)
         
   
if context['MS_IP_filter']:
  MSA_API.task_success('Good, filter IP on all MS (' + ';'.join(context['MS_IP_filter'].keys()) + ') values from '+ context['data_filter_ip_file']+ ', find '+ str(len(interfaces_IP_available)) +' IP availables for given interfaces', context, True)
else:
  MSA_API.task_success('Good, no MS filter available from '+ context['data_filter_ip_file'], context, True)



