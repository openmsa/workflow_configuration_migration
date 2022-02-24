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

context = Variables.task_call(dev_var)
 
# This Script will also remove all given MS values which are not present in the given field :
#    example in 'data_filter_file' file (filter_cisco_IOS_to_XR.txt) we have the line "interface|vrf_name|ip_vrf|object_id", the script  will remove all MS values for the field object_id in the 'ip_vrf' MS where the object_id is not in find in field 'vrf_name' in the 'interface' MS values 


#########################################################
# Function: Parse all MS values recursivly for the given field
def data_find_migrate_recursif(destination_full, fields, ms_newvalues):
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
               data_find_migrate_recursif(destination_full, copy.deepcopy(fields), value1[field]) 
             else:
               if value :
                 if not context.get('Filter_keep_'+destination_full+'_field_values'):
                   context['Filter_keep_'+destination_full+'_field_values'] = {}
                 context['Filter_keep_'+destination_full+'_field_values'][value] = ''
  return 'not found'
   
#########################################################
# Function: Parse all MS values recursivly for the given field
def remove_bad_values_recursif(destination_field_name, fields, ms_newvalues, available_values):
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
               remove_bad_values_recursif(destination_field_name, copy.deepcopy(fields), ms_newvalues[key][field], available_values) 
             else:
               if value:
                 if  value not in available_values:
                   #ms_newvalues[key][field]  = 'IP_TO_REMOVE_value='+value
                   ms_newvalues.pop(key)  #remove parent value
                 #else: 
                   #ms_newvalues[key][field]  = 'OK TO KEEP_value='+value
                 
  return 'not found'

########### ADD LINK #############
MS_list_string        = context['MS_list']  

if not context['enable_filter']:
  MSA_API.task_success('DONE: filter are disabled, no filters applied', context, True)
    
#read filter file
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../'+context['data_filter_file']   # filter_cisco_IOS_to_XR.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  data_filter = file1.read()
  file1.close()
  data_filter_list = data_filter.split('\n')
  data_filter_list = [i for i in data_filter_list if i] #remove empty element
else:
  data_filter_list = ''    
  
context['data_filter'] = data_filter_list
context['data_filter_file_full'] = file 

      
context['MS_to_filter'] = {}

######### IT WILL put migrate to 1 to all destination fields values 
# example for "interface|vrf_name|ip_vrf|object_id"  we keep all MS values for ip_vrf where the object_id is equal to vrf_name in interface MS  and we remove all other MS values

previous_destination_MS_Name    = ''
previous_destination_field_name = ''

if MS_list_string:
  MS_list = MS_list_string.split('\s*;\s*')
  #Find ALL identicals values
  if data_filter_list:
    for line in data_filter_list:
      if (not line.startswith('#')) and line.strip():
        #context['data_filter_line'] = line
        list = line.split('|')  # #orig_MS_Name|orig_field_name|destination_MS_Name|destination_field_name
        if len(list) > 3:
          orig_MS_Name            = list[0]
          orig_field_name         = list[1]
          destination_MS_Name     = list[2]
          destination_field_name  = list[3]
          destination_full = destination_MS_Name + '_' + destination_field_name

          if not previous_destination_MS_Name and not previous_destination_field_name:
            previous_destination_MS_Name    = destination_MS_Name
            previous_destination_field_name = destination_field_name 
            context['Filter_keep_'+destination_full+'_field_values'] = {}

          if  destination_MS_Name != previous_destination_MS_Name or destination_field_name != previous_destination_field_name:
            #we are using now one other destination MS and fieldname, we should clean the previous MS values
            #Remove old unsed values :
            fields = previous_destination_field_name.split('.0.')
            remove_bad_values_recursif(previous_destination_field_name, fields, context[previous_destination_MS_Name+'_values'], context['Filter_keep_'+previous_destination_MS_Name+'_'+previous_destination_field_name+'_field_values']);

            previous_destination_MS_Name    = destination_MS_Name
            previous_destination_field_name = destination_field_name 
            context['Filter_keep_'+destination_full+'_field_values'] = {}

          if  context.get(orig_MS_Name+'_values') and context.get(destination_MS_Name+'_values'):
            context['MS_to_filter'][destination_MS_Name] = 1
            context[orig_field_name+'_field_values'] = {}
            fields = orig_field_name.split('.0.')
            ## Find all source values
            data_find_migrate_recursif(destination_full, fields,context[orig_MS_Name+'_values'])
          else:
            #if not context.get(orig_MS_Name+'_values'):
            #  context['Filter_keep_'+destination_full+'_field_values'] = {}
            if not context.get(destination_MS_Name+'_values'):
              context[destination_MS_Name+'_values'] = {}           


  if destination_MS_Name and destination_field_name:
    #Remove old unsed values :
    destination_full = destination_MS_Name + '_' + destination_field_name
    fields = destination_field_name.split('.0.')

    remove_bad_values_recursif(destination_field_name, fields, context[destination_MS_Name+'_values'], context['Filter_keep_'+destination_full+'_field_values']);
            
   
MSA_API.task_success('DONE: filter all microservices (' + ';'.join(context['MS_to_filter']) + ') values from ' + context['data_filter_file'], context, True)


