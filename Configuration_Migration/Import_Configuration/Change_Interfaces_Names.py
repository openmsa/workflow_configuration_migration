import json
import typing
import os
import copy

from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()

dev_var = Variables()

context = Variables.task_call(dev_var)


#########################################################
# Function: Parse all MS values recursivly for the given field
def change_interfaces_names_recursif(source_field, fields, ms_newvalues, new_interfaces_names, new_interfaces_names_clean):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
    
  if field:
    if isinstance(ms_newvalues, dict):
      if field == 'KEY':
        for old_interface_name, new_interface_name in new_interfaces_names_clean.items():
          if ms_newvalues.get(old_interface_name):
            ms_newvalues[new_interface_name] = ms_newvalues[old_interface_name]
            del ms_newvalues[old_interface_name] 
      else: 
        for  key, value1 in ms_newvalues.items():
          if isinstance(value1, dict):
            if value1.get(field):
               value = value1[field]
               if isinstance(value, dict):
                 change_interfaces_names_recursif(source_field, copy.deepcopy(fields), value1[field], new_interfaces_names, new_interfaces_names_clean) 
               else:
                 if value :
                   if new_interfaces_names.get(value):
                     ms_newvalues[key][field] = new_interfaces_names[value]

  return 'not found'
  
  
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
  MSA_API.task_error('Can not open file "' + file + '"', context, True)
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



