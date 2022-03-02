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
  data_filter_list = ''    
  
context['data_filter'] = data_filter_list
context['data_filter_file_full'] = file 
context['MS_to_filter'] = {}

######### IT WILL put migrate to 1 to all destination fields values 
# example for "interface|vrf_name|ip_vrf|object_id"  we keep all MS values for ip_vrf where the object_id is equal to vrf_name in interface MS  and we remove all other MS values

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
          if  context.get(orig_MS_Name+'_values') and context.get(destination_MS_Name+'_values'):
            context['MS_to_filter'][destination_MS_Name] = 1
            context[orig_field_name+'_field_values'] = {}
            fields = orig_field_name.split('.0.')
            context['Filter_'+orig_field_name+'_field_values'] = {}
            ## Find all source values
            data_find_migrate_recursive(orig_field_name, fields,context[orig_MS_Name+'_values'])
          else:
            if not context.get(orig_MS_Name+'_values'):
              context['Filter_'+orig_field_name+'_field_values'] = {}
            if not context.get(destination_MS_Name+'_values'):
              context[destination_MS_Name+'_values'] = {}           
              context['Filter_'+orig_field_name+'_field_values'] = {}

          fields = destination_field_name.split('.0.')
          remove_bad_values_recursif(destination_field_name, fields, context[destination_MS_Name+'_values'], context['Filter_'+orig_field_name+'_field_values']);
            
   
msg = 'DONE: filter all microservices (' + ';'.join(context['MS_to_filter']) + ') values from ' + context['data_filter_file']
#create_event(device_id_full, "1", "1", subtenant_ref, subtenant_id, msg)
MSA_API.task_success(msg, context, True)