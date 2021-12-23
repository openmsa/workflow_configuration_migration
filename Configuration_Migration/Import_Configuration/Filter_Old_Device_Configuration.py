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
dev_var.add('data_filter', var_type='String')

context = Variables.task_call(dev_var)
 
 

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
   
   
 
#get device_id from context
device_id = context['destination_device_id'][3:]

########### ADD LINK #############
MS_list_string        = context['MS_list']  

now = datetime.now() # current date and time
day = now.strftime("%m-%d-%Y-%H:%m")
    
    
#read filter file
file='/opt/fmc_repository/Datafiles/' + context['data_filter_file']   # filter_cisco_IOS_to_XR.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  data_filter = file1.read()
  file1.close()
  data_filter_list = data_filter.split('\n')
else:
  data_filter_list = ''    
  
context['data_filter'] = data_filter_list

# Start with THE INTERFACE MS
# We wan keeep only interface names whic are given in context['source_interfaces_name']
source_interfaces_name      = context['source_interfaces_name']
source_interfaces_name_list = source_interfaces_name.split('\s*;\s*')

if context.get('interface_values') and not context.get('interface_values_orig'):
  context['interface_values_orig'] = copy.deepcopy(context['interface_values'])

if context.get('interface_values'):
  interfaces_newvalues = context['interface_values']
  #interfaces_newvalues: { "Multilink45": { "object_id": "Multilink45", "migrate": "0",....
  for interface in interfaces_newvalues:
    if interface in source_interfaces_name_list:
      #We used this interface
      interfaces_newvalues[interface]['migrate'] = 1 

context['MS_to_filter'] = {}

if MS_list_string:
  MS_list = MS_list_string.split('\s*;\s*')
  #CONVERT SOME DATA
  if data_filter_list:
    for line in data_filter_list:
      if (not line.startswith('#')) and line.strip():
        context['data_filter_line'] = line
        list = line.split('|')  # #orig_MS_Name|orig_field_name|destination_MS_Name|destination_field_name
        if len(list) > 3:
          orig_MS_Name            = list[0]
          orig_field_name         = list[1]
          destination_MS_Name     = list[2]
          destination_field_name  = list[3]
          context['MS_to_filter'][destination_MS_Name] = 1
          if  context.get(orig_MS_Name+'_values') and context.get(destination_MS_Name+'_values'):
            if not context.get(destination_MS_Name+'_values_orig'):
              context[destination_MS_Name+'_values_orig'] = copy.deepcopy(context[destination_MS_Name+'_values'])
             
            context[orig_field_name+'_field_values'] = {}
            fields = orig_field_name.split('.0.')
            data_find_migrate_recursif(orig_field_name, fields,context[orig_MS_Name+'_values']);
            if context[orig_field_name+'_field_values']:
              for field_value in context[orig_field_name+'_field_values']:
                if destination_field_name == 'object_id':
                  context[destination_MS_Name+'_values'][field_value]['migrate'] = 1
                else:
                  #loop on all object_id to get the good value
                  for  value2 in context[destination_MS_Name+'_values']:
                    #context['zzz_filter'] = context[destination_MS_Name+'_values'][value2] + ' filedval='+field_value
                    if context[destination_MS_Name+'_values'][value2][destination_field_name] == field_value:
                      context[destination_MS_Name+'_values'][value2]['migrate'] = 1 
                    #MSA_API.task_error('LED destination_field_name='+destination_field_name+' val2='+value2 + ' filedval='+field_value, context, True)
 
                  
    for MS in context['MS_to_filter']:
      if context.get(MS+'_values') and context[MS+'_values']:
        ms_newvalues = copy.deepcopy(context[MS+'_values'])
        for  object_id, value in ms_newvalues.items():
          if value.get('migrate') and value['migrate']==0:
            context[MS+'_values'].pop(object_id)  #remove value
            
   
MSA_API.task_success('Good, filter all MS (' + ';'.join(context['MS_to_filter']) + ') values', context, True)



