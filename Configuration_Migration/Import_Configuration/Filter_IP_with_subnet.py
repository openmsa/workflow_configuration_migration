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

IP_available_title = 'IP_available_for_MS_'

MS_list_string        = context['MS_list']  


if not context['enable_filter']:
  MSA_API.task_success('DONE: filter are disabled, no filters applied', context, True)


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

source_interfaces_name_list = context['source_interfaces_name_list']
interfaces_IP_available = {}
    
#############################################
#Get all filter to apply from given file
#############################################
previous_destination_MS_Name                     =''
previous_destination_field_name = ''
if ip_data_filter_list:
  for line in ip_data_filter_list:
    if (not line.startswith('#')) and line.strip():
      #context['data_ip_filter_line'] = line
      list = line.split('|')  # #Source Microservice Name|source variable name IP|source variable name mask|destination Microservice Name|destination variable name
      if len(list) > 4:
        line={}
        source_MS_Name          = list[0]
        source_field_Name_IP    = list[1]
        source_field_Name_mask  = list[2]
        destination_MS_Name     = list[3]
        destination_field_name  = list[4]    
       
        if previous_destination_MS_Name and previous_destination_field_name and (previous_destination_MS_Name != destination_MS_Name or destination_field_name != previous_destination_field_name):
          #############################################
          # remove unwanted data for previous filter MS line 
          #############################################
          context['MS_IP_filter'][previous_destination_MS_Name] = 1
          if context.get(previous_destination_MS_Name+'_values_serialized'):             
            fields = previous_destination_field_name.split('.0.')
            ms_values = json.loads(context[previous_destination_MS_Name+'_values_serialized'])
            remove_bad_ip_values_recursif(previous_destination_field_name, fields, ms_values, context[IP_available_title+previous_destination_MS_Name]);
            context[previous_destination_MS_Name+'_values_serialized'] = json.dumps( ms_values )

        previous_destination_MS_Name = destination_MS_Name
        previous_destination_field_name = destination_field_name
        
        #############################################
        #Get all IP available for all destination_MS_Name:
        # rq: each destination_MS_Name have one different list but we cumul different lines (source) per destination_MS_Name 
        #############################################   
         
        if context.get(IP_available_title+destination_MS_Name):
          #cumul with previous line
          interfaces_IP_available  = context[IP_available_title+destination_MS_Name]
        else:
          interfaces_IP_available  = {}
        
        if context.get(source_MS_Name+'_values_serialized'):
          sources_values = json.loads(context[source_MS_Name+'_values_serialized'])
          #interfaces_newvalues: { "Serial1/0/0_1/3/1/1:0": { "object_id": "Serial1/0/0.1/3/1/1:0", "addresses": { "0": { "ipv4_address": "186.239.124.197", "ipv4_mask": "255.255.255.252" }

          for interface, interface_value in sources_values.items():
            if interface_value.get("object_id"):
              interface_full_name = interface_value["object_id"]    #=Serial1/0/0.1/3/1/1:0, interface=Serial1/0/0_1/3/1/1:0
              #source_field_Name_IP   = addresses.0.ipv4_address
              #source_field_Name_mask = addresses.0.ipv4_mask
              fields = source_field_Name_IP.split('.0.')
              fields_mask = source_field_Name_mask.split('.0.')
              #ipv6_address|ipv6_prefix 
              #addresses.0.ipv4_address
              if isinstance(fields, typing.List) and fields and len(fields) > 1:
                first_level  = fields[0]  # "addresses"
                second_level = fields[1]
                if isinstance(fields_mask, typing.List) and fields_mask and len(fields_mask) > 1:
                  second_level_mask = fields_mask[1]
                  mask_static = False
                else:
                  second_level_mask = source_field_Name_mask
                  mask_static = True

                if interface_value.get(first_level):
                  addresses = interface_value[first_level]
                  if  'ipv4' in second_level:
                    #IPV4 part :
                    for key, address in addresses.items():
                      ipv4_address = address[second_level]
                      if mask_static:
                        ipv4_mask  = second_level_mask        
                      else:
                        ipv4_mask  = address[second_level_mask]          
                      interfaces_IP_available = find_all_ip_in_subnet_ipv4(interface_full_name+'_'+key, ipv4_address, ipv4_mask, interfaces_IP_available)
                  if 'ipv6' in second_level:
                    #IPV6 part :
                    if interface_value.get(second_level):
                      ipv6_address = interface_value[second_level].lower()
                      if mask_static:
                        ipv6_prefix = second_level_mask
                      else:
                        ipv6_prefix = interface_value[second_level_mask]
                        
                      interfaces_IP_available = find_all_ip_in_subnet_ipv6(interface_full_name+'_direct', ipv6_address, ipv6_prefix, interfaces_IP_available)
                    else:
                      #extract from addresses
                      for key, address in addresses.items():
                        if address.get(second_level):
                          ipv6_address = address[second_level].lower()
                          if mask_static:
                            ipv6_prefix = second_level_mask
                          else:
                            ipv6_prefix = address[second_level_mask]
                      
                          interfaces_IP_available = find_all_ip_in_subnet_ipv6(interface_full_name+'_'+key, ipv6_address, ipv6_prefix, interfaces_IP_available)
                    
              else:
                #direct field like  interface|ipv6_address|ipv6_prefix|
                if interface_value.get(source_field_Name_IP) and interface_value.get(source_field_Name_mask):
                  ipv6_address =  interface_value[source_field_Name_IP]
                  ipv6_prefix  =  interface_value[source_field_Name_mask]
                  interfaces_IP_available = find_all_ip_in_subnet_ipv6(interface_full_name+'_', ipv6_address, ipv6_prefix, interfaces_IP_available) 
                
              
        context[IP_available_title+destination_MS_Name] = interfaces_IP_available      

      context['MS_IP_filter'] = {}

#############################################
# remove unwanted data for last filter MS line 
#############################################
if previous_destination_MS_Name and previous_destination_field_name:
  #############################################
  # remove unwanted data for previous filter MS line 
  #############################################
  context['MS_IP_filter'][previous_destination_MS_Name] = 1
  if context.get(previous_destination_MS_Name+'_values_serialized'):             
    fields = previous_destination_field_name.split('.0.')
    ms_values = json.loads(context[previous_destination_MS_Name+'_values_serialized'])
    remove_bad_ip_values_recursif(previous_destination_field_name, fields, ms_values, context[IP_available_title+previous_destination_MS_Name]);
    context[previous_destination_MS_Name+'_values_serialized'] = json.dumps( ms_values )

   
if context['MS_IP_filter']:
  MSA_API.task_success('DONE, filter IP on all microservices (' + ';'.join(context['MS_IP_filter'].keys()) + ') values from '+ context['data_filter_ip_file']+ ', found '+ str(len(interfaces_IP_available)) +' IP availables for the selected interfaces', context, True)
else:
  MSA_API.task_success('DONE, no microservice filter available for '+ context['data_filter_ip_file'], context, True)



