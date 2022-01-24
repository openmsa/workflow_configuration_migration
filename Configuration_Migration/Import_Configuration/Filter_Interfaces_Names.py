import json
import copy
import typing
import os.path
import sys
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime

dev_var = Variables()

dev_var.add('customer_id', var_type='String')
dev_var.add('interfaces.0.source', var_type='String')
dev_var.add('data_filter', var_type='String')
dev_var.add('enable_filter', var_type='Boolean')

INTERFACE = 'interface'

context = Variables.task_call(dev_var)
 
# This Script will filter interfaces names : it remove all interfaces values in INTERFACE MS which are not present in the given field 'interfaces.0.source'


#########################################################
# Function: Parse all MS values recursivly for the given field
def data_find_migrate_recursif(orig_field_name, fields, ms_newvalues):
  if isinstance(fields, typing.List) and fields:
    field = fields[0]
    fields.pop(0)
  else:
    field = fields  #string
  if field:
    if isinstance(ms_newvalues, dict):
      for  key, value1 in ms_newvalues.items():
        if isinstance(value1, dict):
          if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               data_find_migrate_recursif(orig_field_name, copy.deepcopy(fields), value1[field]) 
             else:
               if value :
                 context[orig_field_name+'_field_values'][value] = ''
  return 'not found'
   

########### ADD LINK #############
MS_list_string        = context['MS_list']  


if not context['enable_filter']:
  MSA_API.task_success('DONE: filter are disabled, no filters applied', context, True)

# Start with THE INTERFACE MS
# We wan keep only interface names which are given in context['interfaces.0.source']

source_interfaces_name_list = []

if context.get('interfaces'):
  interfaces = context['interfaces']
  for interface in interfaces:
    if interface.get('source'):
      source_interfaces_name_list.append(interface['source'])

context['source_interfaces_name_list'] = source_interfaces_name_list

nb_interfaces_found = 0
interfaces_found    = []
interfaces_MS_found = []

if context.get(INTERFACE+'_values'):
  interfaces_newvalues = context[INTERFACE+'_values']
  #interfaces_newvalues: { "Multilink45": { "object_id": "Multilink45", "migrate": "0",....
  for interface, val in interfaces_newvalues.items():
    if val.get('object_id'):
      interface_orig = val["object_id"] #we get the object_id where the interface name is original (the '.' is not replace with '_' in interface name) ex GigabitEthernet0/0/1.1561501
      interfaces_MS_found.append(interface_orig)
      if interface_orig in source_interfaces_name_list:
        #We used this interface
        interfaces_found.append(interface_orig)
        interfaces_newvalues[interface]['migrate'] = 1 
        nb_interfaces_found=nb_interfaces_found+1
      
   
context['interfaces_found from MS'] = interfaces_found  
 
if nb_interfaces_found:   
  if context.get(INTERFACE+'_values') and context[INTERFACE+'_values']:
    ms_newvalues = copy.deepcopy(context[INTERFACE+'_values']) # We can not remove one element while iterating over it, so itirating on one ms_newvalues
    for  object_id, value in ms_newvalues.items():
      if not value.get('migrate') or value['migrate'] == 0:
        context[INTERFACE+'_values'].pop(object_id)  #remove value
        
  MSA_API.task_success('DONE: found '+str(nb_interfaces_found)+' interfaces (' + ', '.join(interfaces_found) + ')', context, True)
  
else:
  MSA_API.task_error('ERROR: cannot find any interfaces: (' + ', '.join(source_interfaces_name_list) + '), , interfaces found: (' + ', '.join(interfaces_MS_found) + ')', context, True)


