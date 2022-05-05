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
#dev_var.add('interfaces.0.pseudowire_ip' )
dev_var.add('interfaces.0.pseudowire_class' )
#dev_var.add('interfaces.0.gil' )

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
  MSA_API.task_error('Can not open file "' + file + '"', context, True)
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
        key = fields[0] +'|'+ destination_MS_Name
        if isinstance(fields, typing.List) and fields and (len(fields) > 1):
          #interfaces.0.destination
          if not wf_fields.get(key):
            wf_fields[key] = {}
          if not wf_fields[key].get('second_level'):
            wf_fields[key]['second_level'] = []
            wf_fields[key]['destination_field_name'] = []
          wf_fields[key]['second_level'].append(fields[1])
          wf_fields[key]['destination_MS_Name'] = destination_MS_Name
          wf_fields[key]['destination_field_name'].append(destination_field_name)
        else:
          #fields is a simple field
          if not wf_fields.get(key):
            wf_fields[key]  = {}
          if not wf_fields[key].get('second_level'):
            wf_fields[key]['second_level'] = []
            wf_fields[key]['destination_field_name'] = []
          wf_fields[key]['destination_MS_Name'] = destination_MS_Name
          wf_fields[key]['destination_field_name'].append(destination_field_name)

#context['import_wf_fields'] =  wf_fields

'''     "import_wf_fields": {
        "interfaces|xconnect": {
            "second_level": [
                "xconnect_group",
                "destination",
                "pseudowire_id",
                "pseudowire_class",
            ],
            "destination_field_name": [
                "object_id",
                "groups.0.interface",
                "groups.0.pseudowire_id",
                "groups.0.pseudowire_class",
            ],
            "destination_MS_Name": "xconnect"
        },
        "'ELINE_'+customer_id|xconnect": {
            "second_level": [],
            "destination_field_name": [
                "groups.0.p2p"
            ],
            "destination_MS_Name": "xconnect"
        },
        "interfaces|interface": {
            "second_level": [
                "destination",
                "dot1q",
                "second_dot1q"
            ],
            "destination_field_name": [
                "object_id",
                "encapsulation_dot1q",
                "encapsulation_second_dot1q"
            ],
            "destination_MS_Name": "interface"
        },
        "customer_id|interface": {
            "second_level": [],
            "destination_field_name": [
                "customer_name"
            ],
            "destination_MS_Name": "interface"
        }
    },
'''

object_id =''
object_id_without_point =''

#Get original fields values
for source_key,item  in wf_fields.items():
    #We should fill one array
    value = {}
    count = 0
    current_object_id = ''
    key = source_key.split('|')   #first_wf_field|destination_MS_Name
    first_wf_field = key[0]
    if context.get(first_wf_field) and context[first_wf_field]:
      if item['second_level']:
        for context_val in context[first_wf_field]:
          #context['import_wf_'+first_wf_field+'_count'+str(count)] = context_val
          ''' context_val =>
              "import_wf_interfaces_count0": {
              "source": "Serial2/3/0.1/3/6/2:0",
              "destination": "BBSerial2/3/0.1/3/6/2:0",
              "xconnect_group": "PWHE_FAT",
              "dot1q": "LOLOdout1",
              "second_dot1q": "LOLOdot1Sec",
              "pseudowire_id": "1700",
              "pseudowire_class": "pseudowire_class1",
          '''
          for idx, second_field in enumerate(item['second_level']) :
            if context_val.get(second_field) and item['destination_field_name'][idx]:
              destination_field_name = item['destination_field_name'][idx]
              if destination_field_name == 'object_id':
                object_id = context_val[second_field]
                object_id_without_point = object_id.replace('.','_')
                if current_object_id != object_id:
                  destMS = item['destination_MS_Name']+'_values'
                  if context.get(destMS) and context[destMS] and context[destMS].get(object_id_without_point):
                    value = context[destMS][object_id_without_point]
                  else:
                    value = {}
                  count = 0
                  current_object_id = object_id
                  value['object_id'] = object_id
              else:
                fields = destination_field_name.split('.0.')  # groups.0.pseudowire_id
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
                else:
                  value[destination_field_name] =  context_val[second_field]
              
              #value[item['destination_field_name'][idx]] = context_val[second_field] 
          if context.get(item['destination_MS_Name']+'_values'):
            newvalue = context[item['destination_MS_Name']+'_values']
          else:
            newvalue = {}
          if value and object_id:
            newvalue[object_id_without_point] = value
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
        if context.get(item['destination_MS_Name']+'_values'):
          destination_MS_context = context[item['destination_MS_Name']+'_values']
        else:
          destination_MS_context = {}
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
        else:
          for objectid, val in destination_MS_context.items():
            val[item['destination_field_name'][0]] = newval

MSA_API.task_success('DONE: Insert workflow parameters into microservices', context, True)



