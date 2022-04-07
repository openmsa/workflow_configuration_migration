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
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()

INTERFACE = 'interface'

context = Variables.task_call(dev_var)
subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]
device_id_full = context['source_device_id_full']

# This Script will filter interfaces names : it remove all interfaces values in INTERFACE MS which are not present in the given field 'interfaces.0.source'

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
  msg = 'ERROR: cannot find the interfaces: (' + ', '.join(source_interfaces_name_list) + ')'
  create_event(device_id_full, "1", "MIGRATION", "FILTER", subtenant_ref, subtenant_id, msg)
  MSA_API.task_error(msg, context, True)
