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
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()

context = Variables.task_call(dev_var)

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
  MSA_API.task_error('Can not open file "' + file + '"', context, True)
  ip_data_filter_list = ''    
  
context['IP_data_filter'] = ip_data_filter_list


#if context.get('interface_values') and not context.get('interface_values_orig'):
#  context['interface_values_orig'] = copy.deepcopy(context['interface_values'])

if not context['enable_filter']:
  MSA_API.task_success('DONE: filter are disabled, no filters applied', context, True)

source_interfaces_name_list = context['source_interfaces_name_list']
interfaces_IP_available = {}
    
if context.get('interface_values'):
  interfaces_values = context['interface_values']
  #interfaces_newvalues: { "Serial1/0/0_1/3/1/1:0": { "object_id": "Serial1/0/0.1/3/1/1:0", "addresses": { "0": { "ipv4_address": "186.239.124.197", "ipv4_mask": "255.255.255.252" }
  for interface, interface_value in interfaces_values.items():
    if interface_value.get("object_id"):
      interface_full_name = interface_value["object_id"]    #=Serial1/0/0.1/3/1/1:0, interface=Serial1/0/0_1/3/1/1:0
      if interface_full_name in source_interfaces_name_list:
        if interface_value.get("addresses"):
          addresses = interface_value["addresses"]
          #IPV4 part :
          for key, address in addresses.items():
            ipv4_address = address["ipv4_address"]
            ipv4_mask    = address["ipv4_mask"]          
            interfaces_IP_available = find_all_ip_in_subnet_ipv4(interface_full_name+'_'+key, ipv4_address, ipv4_mask, interfaces_IP_available)
          #IPV6 part :
          if interface_value.get("ipv6_address") and interface_value.get("ipv6_prefix"):
            ipv6_address = interface_value["ipv6_address"]
            ipv6_prefix = interface_value["ipv6_prefix"]
            interfaces_IP_available = find_all_ip_in_subnet_ipv6(interface_full_name+'_'+key, ipv6_address, ipv6_prefix, interfaces_IP_available)

context['interfaces_IP_available'] = interfaces_IP_available      


context['MS_IP_filter'] = {}

if MS_list_string:
  MS_list = MS_list_string.split('\s*;\s*')
  # FILTER SOME DATA with IP
  if ip_data_filter_list:
    for line in ip_data_filter_list:
      if (not line.startswith('#')) and line.strip():
        #context['data_ip_filter_line'] = line
        list = line.split('|')  # #MS_Name|field_name
        if len(list) > 1:
          MS_Name     = list[0]
          field_name  = list[1]
          context['MS_IP_filter'][MS_Name] = 1
          if context.get(MS_Name+'_values'):             
            fields = field_name.split('.0.')
            remove_bad_ip_values_recursif(field_name, fields, context[MS_Name+'_values'], interfaces_IP_available);
            

#MSA_API.task_error('TETS33T22  '+ context['data_filter_ip_file'], context, True)
         
   
if context['MS_IP_filter']:
  MSA_API.task_success('DONE, filter IP on all microservices (' + ';'.join(context['MS_IP_filter'].keys()) + ') values from '+ context['data_filter_ip_file']+ ', found '+ str(len(interfaces_IP_available)) +' IP availables for the selected interfaces', context, True)
else:
  MSA_API.task_success('DONE, no microservice filter available for '+ context['data_filter_ip_file'], context, True)



