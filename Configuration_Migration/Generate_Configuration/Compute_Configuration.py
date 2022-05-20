import json
import copy
import typing
import os
import os.path
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

#check if the folder  DIRECTORY exist, else create it
if not os.path.isdir(DIRECTORY):
 os.mkdir(DIRECTORY)

########### LOOP ON ALL GIVEN MS #############
MS_list        = context['MS_list']  
MS_list        = MS_list.replace('\s*;\s*',';')     

now = datetime.now() # current date and time
day = now.strftime("%m-%d-%Y-%Hh%M")
    
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../' + context['data_conversion_pattern_file']
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  data_conversion = file1.read()
  file1.close()
  data_conversion_list = data_conversion.split('\n')
  data_conversion_list = [i for i in data_conversion_list if i] #remove empty element
else:
  MSA_API.task_error('Can not open file "' + file + '"', context, True)
  data_conversion_list = ''    
context['data_conversion'] = data_conversion_list


if MS_list:
  for MS in  MS_list.split(';'):
    if MS:

      #########################################################
      # CONVERT SOME MS VALUES FROM THE CONVERTION PATTERN FILE
      if data_conversion_list:
        for line in data_conversion_list:
          if (not line.startswith('#')) and line.strip():
            context['data_conversion_line'] = line+';'
            list = line.split('|')  # MS|Field|Replace Pattern|comment
            if len(list) > 4:
              convert_MS             = list[0]
              convert_field          = list[1]
              convert_condition      = list[2]
              convert_pattern_source = list[3]
              convert_pattern_destination = list[4]
              convert_comment = list[5]

              if convert_MS == MS and context.get(MS+'_values_serialized'):
                ms_newvalues = json.loads(context[MS+'_values_serialized'])
                fields = convert_field.split('.0.')
                data_conversion_recursif_compute_conf(ms_newvalues, fields, convert_condition, convert_pattern_source, convert_pattern_destination)
                     
            
      #########################################################
      # ADD THE DOWNLOAD FILE LINK FOR EACH VALUES
      link =      DIRECTORY + "/" + MS + context['SERVICEINSTANCEID'] + '_'  + day + '.txt'
      link_orig = DIRECTORY + "/" + MS + context['SERVICEINSTANCEID'] + '_'  + day + '_orig.txt'
      
      context[MS + '_link'] = link
      context[MS + '_link_orig'] = link_orig



context['generate_file'] = DIRECTORY+ "/" + "ALL_MS_" + context['SERVICEINSTANCEID'] + "_" + day + '.txt'

MSA_API.task_success('DONE: update the interfaces names and compute data from '+ context['data_conversion_pattern_file'], context, True)



