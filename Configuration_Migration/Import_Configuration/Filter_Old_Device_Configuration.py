import os.path
import sys
import typing
import copy
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

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]
device_id_full = context['source_device_id_full']


#########################################################

# Function: Parse all MS values recursivly for the given field
def data_find_migrate_recursif(destination_full, fields, ms_newvalues):
  global filter_keep_field_values
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
                 if not filter_keep_field_values.get('Filter_keep_'+destination_full+'_field_values'):
                   filter_keep_field_values['Filter_keep_'+destination_full+'_field_values'] = {}
                 filter_keep_field_values['Filter_keep_'+destination_full+'_field_values'][value] = ''
  return 'not found'

#########################################################
# Function: Parse all MS values recursivly for the given field
def change_interfaces_names_recursive(source_field, fields, ms_newvalues, new_interfaces_names, new_interfaces_names_clean):
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
                 change_interfaces_names_recursive(source_field, copy.deepcopy(fields), value1[field], new_interfaces_names, new_interfaces_names_clean) 
               else:
                 if value :
                   if new_interfaces_names.get(value):
                     ms_newvalues[key][field] = new_interfaces_names[value]

  return 'not found'

# This Script will also remove all given MS values which are not present in the given field :
#    example in 'data_filter_file' file (filter_cisco_IOS_to_XR.txt) we have the line "interface|vrf_name|ip_vrf|object_id", the script  will remove all MS values for the field object_id in the 'ip_vrf' MS where the object_id is not in find in field 'vrf_name' in the 'interface' MS values 

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
  MSA_API.task_error('Can not open file "' + file + '"', context, True)
  data_filter_list = ''    
  
#context['data_filter'] = data_filter_list
context['data_filter_file_full'] = file 
context['MS_to_filter'] = {}

######### IT WILL put migrate to 1 to all destination fields values 
# example for "interface|vrf_name|ip_vrf|object_id"  we keep all MS values for ip_vrf where the object_id is equal to vrf_name in interface MS  and we remove all other MS values


previous_destination_MS_Name    = ''
previous_destination_field_name = ''
filter_keep_field_values        = {}

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
            filter_keep_field_values['Filter_keep_'+destination_full+'_field_values'] = {}

          if  destination_MS_Name != previous_destination_MS_Name or destination_field_name != previous_destination_field_name:
            #we are using now one other destination MS and fieldname, we should clean the previous MS values
            #Remove old unsed values :
            fields = previous_destination_field_name.split('.0.')
            ms_values = json.loads(context[previous_destination_MS_Name+'_values_serialized'])
            remove_bad_values_recursif(previous_destination_field_name, fields, ms_values, filter_keep_field_values['Filter_keep_'+previous_destination_MS_Name+'_'+previous_destination_field_name+'_field_values']);
            context[previous_destination_MS_Name+'_values_serialized'] = json.dumps( ms_values )

            previous_destination_MS_Name    = destination_MS_Name
            previous_destination_field_name = destination_field_name 
            filter_keep_field_values['Filter_keep_'+destination_full+'_field_values'] = {}

          if  context.get(orig_MS_Name+'_values_serialized') and context.get(destination_MS_Name+'_values_serialized'):
            context['MS_to_filter'][destination_MS_Name] = 1
            #context[orig_field_name+'_field_values'] = {}
            fields = orig_field_name.split('.0.')
            ## Find all source values

            ms_values = json.loads(context[orig_MS_Name+'_values_serialized'])
            data_find_migrate_recursif(destination_full, fields, ms_values)
            context[orig_MS_Name+'_values_serialized'] = json.dumps( ms_values )


          else:
            if not context.get(destination_MS_Name+'_values_serialized'):
              context[destination_MS_Name+'_values_serialized'] = json.dumps({})          

  if destination_MS_Name and destination_field_name:
    #Remove old unsed values :
    destination_full = destination_MS_Name + '_' + destination_field_name
    fields = destination_field_name.split('.0.')

    ms_values = json.loads(context[destination_MS_Name+'_values_serialized'])
    remove_bad_values_recursif(destination_field_name, fields, ms_values, filter_keep_field_values['Filter_keep_'+destination_full+'_field_values']);
    context[destination_MS_Name+'_values_serialized'] = json.dumps( ms_values )

msg = 'DONE: filter all microservices (' + ';'.join(context['MS_to_filter']) + ') values from ' + context['data_filter_file']
#create_event(device_id_full, "1", "1", subtenant_ref, subtenant_id, msg)
MSA_API.task_success(msg, context, True)