import json
import typing
import os
from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()

dev_var = Variables()
dev_var.add('interfaces.0.source' )
dev_var.add('interfaces.0.destination' )
dev_var.add('interfaces.0.xconnect_group' )
dev_var.add('interfaces.0.dot1q' )
dev_var.add('interfaces.0.second_dot1q' )
dev_var.add('interfaces.0.pseudowire_id' )
dev_var.add('interfaces.0.pseudowire_ip' )
dev_var.add('interfaces.0.pseudowire_class' )
dev_var.add('interfaces.0.gil' )

context = Variables.task_call(dev_var)




    
#read import_WF_parameters_into_MS.txt file
wf_path = os.path.dirname(__file__)
file =  wf_path+'/../'+context['import_WF_parameters_into_MS_file']   # import_WF_parameters_into_MS.txt
if os.path.isfile(file):
  file1 = open(file, "r")
  # read file content
  import_liste = file1.read()
  file1.close()
  import_liste_list = import_liste.split('\n')
  import_liste_list = [i for i in import_liste_list if i] #remove empty element
else:
  import_liste_list = ''    
  
context['import_liste'] = import_liste_list
context['import_liste_file_full'] = file 

wf_fields = {}

if import_liste_list:
  for line in import_liste_list:
    if (not line.startswith('#')) and line.strip():
      #context['data_filter_line'] = line
      list = line.split('|')  # #orig_MS_Name|orig_field_name|destination_MS_Name|destination_field_name
      if len(list) > 2:
        orig_field_name         = list[0]
        destination_MS_Name     = list[1]
        destination_field_name  = list[2]
        fields = orig_field_name.split('.0.')
        if isinstance(fields, typing.List) and fields and (len(fields) > 1):
          #interfaces.0.destination
          if not wf_fields.get(fields[0]):
            wf_fields[fields[0]] = {}
          if not wf_fields[fields[0]].get('second_level'):
            wf_fields[fields[0]]['second_level'] = []
            wf_fields[fields[0]]['destination_field_name'] = []
          wf_fields[fields[0]]['second_level'].append(fields[1])
          wf_fields[fields[0]]['destination_MS_Name'] = destination_MS_Name
          wf_fields[fields[0]]['destination_field_name'].append(destination_field_name)
        else:
          #fields is a simple field
          if not wf_fields.get(fields[0]):
            wf_fields[fields[0]]  = {}
          if not wf_fields[fields[0]].get('second_level'):
            wf_fields[fields[0]]['second_level'] = []
            wf_fields[fields[0]]['destination_field_name'] = []
          wf_fields[fields[0]]['destination_MS_Name'] = destination_MS_Name
          wf_fields[fields[0]]['destination_field_name'].append(destination_field_name)

context['import_wf_fields'] =  wf_fields


''' "wf_fields": {
        "interfaces": {
            "second_level": [
                "xconnect_group",
                "destination",
                "pseudowire_id",
                "pseudowire_ip",
                "pseudowire_class",
                "gil"
            ],
            "destination_field_name": [
                "object_id",
                "groups.0.interface",
                "groups.0.pseudowire_id",
                "groups.0.pseudowire_ip",
                "groups.0.pseudowire_class",
                "groups.0.gil"
            ],
            "destination_MS_Name": "xconnect"
        },
        "'ELINE_'+customer_id": {
            "second_level": [],
            "destination_field_name": [
                "groups.0.p2p"
            ],
            "destination_MS_Name": "xconnect"
'''

object_id =''

#Get original fields values
for first_wf_field,item  in wf_fields.items():
    #We should fill one array
    value = {}
    count = 0
    current_object_id = ''
    if context.get(first_wf_field) and context[first_wf_field]:
      if item['second_level']:
        for context_val in context[first_wf_field]:
          context['import_wf_'+first_wf_field+'count'+str(count)] = context_val
          for idx, second_field in enumerate(item['second_level']) :
            if context_val.get(second_field) and item['destination_field_name'][idx]:
              destination_field_name = item['destination_field_name'][idx]
              if destination_field_name == 'object_id':
                object_id = context_val[second_field]
                if current_object_id != object_id:
                  value = {}
                  count = 0
                  current_object_id = object_id                
              else:
                fields = destination_field_name.split('.0.')  # groups.0.pseudowire_ip
                if isinstance(fields, typing.List) and fields and (len(fields) > 1):
                  first  = fields[0]
                  second = fields[1]
                  if not value.get(first):
                    value[first]={}
                  if not value[first].get(count):
                    value[first][count]={}              
                  if context_val.get(second_field):
                    value[first][count][second] =  context_val[second_field]
                  else:
                    value[first][count][second] =  "No available"
              #value[item['destination_field_name'][idx]] = context_val[second_field] 
          if context.get(item['destination_MS_Name']+'_values'):
            newvalue = context[item['destination_MS_Name']+'_values']
          else:
            newvalue = {}
          if value and object_id:
            newvalue[object_id] = value
          context[item['destination_MS_Name']+'_values'] = newvalue
          count = count +1
      else:
        #get value directly from the context to add new value to all current values
        fields = first_wf_field.split('+')   
        if isinstance(fields, typing.List) and fields and (len(fields) > 1):
          # first_wf_field = 'ELINE_'+customer_id
          if fields[0].startswith("'") and fields[0].endswith("'"):  #like 'ELINE_'
            newval = fields[0].replace("'",'')
          else:
            newval = context[fields[0]]
          if fields[1].startswith("'") and fields[1].endswith("'"):
            newval = newval + fields[1]
          else:
            newval = newval+ context[fields[1]]        
        else:
          newval = context[first_wf_field] #get value directly from the context
        destination_MS_context = context[item['destination_MS_Name']+'_values']
        fields = item['destination_field_name'][0].split('.0.')  # groups.0.p2p
        if isinstance(fields, typing.List) and fields and (len(fields) > 1):
          first  = fields[0]  # groups
          second = fields[1]  # p2p
          for objectid, val in destination_MS_context.items():
            if val.get(first):          
              for num,valfirts_field in val[first].items():
                valfirts_field[second] = newval
            else:
               val[first]={}
               val[first][second] = newval

MSA_API.task_success('DONE: Insert workflow parameters into microservices', context, True)



