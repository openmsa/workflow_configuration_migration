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
fields_to_report = [ 'object_id', 'name']

#########################################################

# Function: Parse all MS values recursivly for the given field
def find_source_values_recursif(destination_full, fields, ms_newvalues):
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
               find_source_values_recursif(destination_full, copy.deepcopy(fields), value1[field]) 
             else:
               if value :
                 if not filter_keep_field_values.get('Filter_source_'+destination_full+'_field_values'):
                   filter_keep_field_values['Filter_source_'+destination_full+'_field_values'] = {}
                 filter_keep_field_values['Filter_source_'+destination_full+'_field_values'][value] = ''
  return 'not found'
  
# Function: Parse all MS values recursivly for the given field
def find_destination_values_recursif(destination_full, fields, ms_newvalues):
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
               find_destination_values_recursif(destination_full, copy.deepcopy(fields), value1[field]) 
             else:
               if value :
                 if not filter_keep_field_values.get('Filter_destination_'+destination_full+'_field_values'):
                   filter_keep_field_values['Filter_destination_'+destination_full+'_field_values'] = {}
                 filter_keep_field_values['Filter_destination_'+destination_full+'_field_values'][value] = ''
  return 'not found'
 
 
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
  

previous_destination_MS_Name    = ''
previous_destination_field_name = ''
filter_keep_field_values        = {}
error_messages = {}
previous_sources = []
        
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
            filter_keep_field_values['Filter_source_'+destination_full+'_field_values'] = {}
            filter_keep_field_values['Filter_destination_'+destination_full+'_field_values'] = {}

          if  destination_MS_Name != previous_destination_MS_Name or destination_field_name != previous_destination_field_name:
            if previous_destination_field_name in fields_to_report:
              #we don't generate one report/warning if the field_name is not in fields_to_report array
              fields = previous_destination_field_name.split('.0.')
              ms_values = json.loads(context[previous_destination_MS_Name+'_values_serialized'])
              previous_destination_full = previous_destination_MS_Name+'_'+previous_destination_field_name
              find_destination_values_recursif(previous_destination_full, fields, ms_values);
              destination_values = filter_keep_field_values['Filter_destination_'+previous_destination_full+'_field_values']
              source_values = filter_keep_field_values['Filter_source_'+previous_destination_full+'_field_values']

              for value in source_values:
                if value and value not in destination_values:
                  error_messages[previous_destination_MS_Name+ '_' + previous_destination_field_name + '_' + str(value)] =   'MS "' + previous_destination_MS_Name+ '" ' + previous_destination_field_name + ' has missing definition value "'+value+'" from ('+' or '.join(previous_sources) +')'
            
     
            previous_destination_MS_Name    = destination_MS_Name
            previous_destination_field_name = destination_field_name 
            previous_sources = []
            filter_keep_field_values['Filter_source_'+destination_full+'_field_values'] = {}
            filter_keep_field_values['Filter_destination_'+destination_full+'_field_values'] = {}
          
          previous_sources.append(orig_MS_Name+'|'+orig_field_name)

          if  context.get(orig_MS_Name+'_values_serialized') and context.get(destination_MS_Name+'_values_serialized'):
            #context[orig_field_name+'_field_values'] = {}
            fields = orig_field_name.split('.0.')
            ## Find all source values
            ms_values = json.loads(context[orig_MS_Name+'_values_serialized'])
            find_source_values_recursif(destination_full, fields, ms_values)

          else:
            if not context.get(destination_MS_Name+'_values_serialized'):
              context[destination_MS_Name+'_values_serialized'] = json.dumps({})          

  if destination_MS_Name and destination_field_name:
    if destination_field_name in fields_to_report:
      #we don't generate one report/warning if the field_name is not in fields_to_report array
      destination_full = destination_MS_Name + '_' + destination_field_name
      fields = destination_field_name.split('.0.')

      ms_values = json.loads(context[destination_MS_Name+'_values_serialized'])
      source_values = filter_keep_field_values['Filter_source_'+destination_full+'_field_values']
      find_destination_values_recursif(destination_full, fields, ms_values);
      destination_values = filter_keep_field_values['Filter_destination_'+destination_full+'_field_values']
      #context['filter_keep_field_values'] = filter_keep_field_values

      for value in source_values:
        if value and value not in destination_values:
          error_messages[destination_MS_Name+ '_' + destination_field_name + '_' + str(value)] =   'MS "' + destination_MS_Name+ '" ' + destination_field_name + ' has missing definition value "'+value+'" from ('+' or '.join(previous_sources) +')'
 

#check if the folder  DIRECTORY exist, else create it
if not os.path.isdir(DIRECTORY):
 os.mkdir(DIRECTORY)
now = datetime.now() # current date and time
day = now.strftime("%m-%d-%Y-%Hh%M")
 
context['consistency_checking_file'] = DIRECTORY+ "/" + "consistency_checking_" + context['SERVICEINSTANCEID'] + "_" + day + '.txt'
f = open(context['consistency_checking_file'], "w")
f.write('# Check consistency data44\n')
nb_error=0
if error_messages:
  for key,val in error_messages.items():
    f.write(val + '\n')
    nb_error=nb_error+1
f.close()

       
msg = 'DONE: check consistency, found ' + str(nb_error) + ' warning, result in ' + context['consistency_checking_file']
MSA_API.task_success(msg, context, True)