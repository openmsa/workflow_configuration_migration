import json
import typing
import os
import copy
import sys

from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()

context = Variables.task_call(dev_var)
device_id_full = context['source_device_id_full']

MS_list_string        = context['MS_list']  

############# Get new interfaces name from context['interfaces']
source_interfaces_name_list = []
destination_interfaces_name_list = []
new_interfaces_names = {}
new_interfaces_names_clean = {}

if context.get('interfaces'):
  interfaces = context['interfaces']
  for interface in interfaces:
    if interface.get('source'):
      source_interfaces_name_list.append(interface['source'])
    if interface.get('destination'):
      destination_interfaces_name_list.append(interface['destination'])
      if interface.get('source') and interface['destination'] != interface['source']:
        new_interfaces_names[interface['source']] = interface['destination']
        new_interfaces_names_clean[interface['source'].replace('.','_') ] = interface['destination'].replace('.','_')  # replace '.' with '_'

if len(source_interfaces_name_list) != len(destination_interfaces_name_list):
      MSA_API.task_error('ERROR: the length of source interfaces list and target interfaces list are different (old=('+','.join(source_interfaces_name_list)+'), new=('+','.join(destination_interfaces_name_list)+')', context, True)

context['new_interfaces_names'] = new_interfaces_names

#read filter file
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../'+context['change_interfaces_names_file']   # Configuration/change_interfaces_names.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  data_filter = file1.read()
  file1.close()
  change_interface = data_filter.split('\n')
  change_interface = [i for i in change_interface if i] #remove empty element
else:
  change_interface = ''    
  
context['change_interfaces_names'] = change_interface
context['change_interfaces_names_file_full'] = file 

if MS_list_string:
  MS_list = MS_list_string.split('\s*;\s*')
  #Find ALL identicals values
  if change_interface:
    for line in change_interface:
      if (not line.startswith('#')) and line.strip():
        #context['data_filter_line'] = line
        list = line.split('|')  # Microservice Name | Microservice variable   like  interface|object_id
        if len(list) > 1:
          orig_MS_Name            = list[0]
          orig_field_name         = list[1]
          if  context.get(orig_MS_Name+'_values'):
            context[orig_field_name+'_field_values'] = {}
            fields = orig_field_name.split('.0.')
            context['Filter_'+orig_field_name+'_field_values'] = {}
            ## Find all source values
            change_interfaces_names_recursif(orig_MS_Name+'_'+orig_field_name,fields, context[orig_MS_Name+'_values'], new_interfaces_names, new_interfaces_names_clean) 
            
          else:
            if not context.get(orig_MS_Name+'_values'):
              context['Filter_'+orig_field_name+'_field_values'] = {}
           
MSA_API.task_success('DONE: update the interfaces names ', context, True)



