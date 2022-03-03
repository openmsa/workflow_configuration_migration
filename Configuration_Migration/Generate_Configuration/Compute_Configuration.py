import json
import copy
import typing
import os
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime

dev_var = Variables()

context = Variables.task_call(dev_var)

DIRECTORIE = '/opt/fmc_repository/Datafiles/Migration_result'

#########################################################
# Function: Parse all MS values recursivly and change the value (by reference) if needed 
def  data_conversion_recursif(ms_newvalues, fields, convert_condition, convert_pattern_source, convert_pattern_destination):
   if isinstance(fields, typing.List) and fields:
     field = fields[0]
     fields.pop(0)
   else:
     field = fields  #string
   if field:
     if isinstance(ms_newvalues, dict):
       for  key, value1 in ms_newvalues.items():
       #for key in ms_newvalues:
         if isinstance(value1, dict):
           if value1.get(field):
             value = value1[field]
             if isinstance(value, dict):
               data_conversion_recursif(value1[field], copy.deepcopy(fields), convert_condition, convert_pattern_source, convert_pattern_destination) 
             else:
               if value :
                 source=''
                 # CAN NOT used try.... because it will not parse all values in ms_newvalues (try will used only first value), so we used one convert_condition
                 if eval(convert_condition):
                   source      = eval(convert_pattern_source)
                   destination = eval(convert_pattern_destination)
       
                   if source:
                     context['result_source_'+value]      = source
                     context['result_destination_'+value] = destination
                     ms_newvalues[key][field] = value.replace(source,destination)
               
   return 'ok'
   


  

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

              if convert_MS == MS and context.get(MS+'_values'):
                #if  not context.get(MS+'_values_orig'):
                #  context[MS+'_values_orig'] = copy.deepcopy(context[MS+'_values'])
                ms_newvalues = context[MS+'_values']
                fields = convert_field.split('.0.')
                data_conversion_recursif(ms_newvalues, fields, convert_condition, convert_pattern_source, convert_pattern_destination)
                     
            
      #########################################################
      # ADD THE DOWNLOAD FILE LINK FOR EACH VALUES
      config = context.get( MS + '_values')
      link =      DIRECTORIE + "/" + MS + '_'  + day + '.txt'
      link_orig = DIRECTORIE + "/" + MS + '_'  + day + '_orig.txt'
      
      context[MS + '_link'] = link
      context[MS + '_link_orig'] = link_orig



context['generate_file'] = DIRECTORIE+ "/" + "ALL_MS_"  + day + '.txt'

#check if the directorie  DIRECTORIE exist, else create it
if not os.path.isdir(DIRECTORIE):
 os.mkdir(DIRECTORIE)


MSA_API.task_success('DONE: update the interfaces names and compute data from '+ context['data_conversion_pattern_file'], context, True)



