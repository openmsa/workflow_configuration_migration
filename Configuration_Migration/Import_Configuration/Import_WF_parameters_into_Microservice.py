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

context = Variables.task_call(dev_var)

XCONNECT = 'xconnect'


if context.get('xconnect_group'):
  groups = context['xconnect_group']
else:
  group = { 'xconnect_group' : 'PW-HE-TEST', 'source' : 'PW-Ether1600', 'destination' : 'AAPW-Ether1600', 'pseudowire_id' : '1600', 'pseudowire_ip' : '177.61.178.254', 'pseudowire_class' : 'pw-class1', 'gil' : 'gil1'}
  groups = [group]
  context['groups'] = groups

if context.get(XCONNECT+'_values'):
  xconnect_values = context[XCONNECT+'_values']
else:
  xconnect_values = {}

#reset xconnect_values
xconnect_values = {}

values={}
counts = {}
for group in groups:
  value = {}
  groupe_name               = group['xconnect_group']
  value= {}
  value['interface']        = group['destination']
  value['pseudowire_id']    = group['pseudowire_id']
  value['pseudowire_ip']    = group['pseudowire_ip']
  value['pseudowire_class'] = group['pseudowire_class']
  value['gil']              = group['gil']
  if context.get('customer_id'):
    value['p2p']            = 'ELINE_'+context['customer_id']
  
  if not values.get(groupe_name):
    values[groupe_name]            = {}
    values[groupe_name]['groups']  = {}
    counts[groupe_name]            = 0
  else:
    counts[groupe_name] = counts[groupe_name] + 1
  values[groupe_name]['object_id']   = groupe_name
  values[groupe_name]['groups'][counts[groupe_name]] = value

  '''   "xconnect_values": {
        "PW-HE-TEST": {
            "0": {
                "interface": "AAPW-Ether1600",
                "pseudowire_id": "1600",
                "pseudowire_ip": "177.61.178.254",
                "pseudowire_class": "pw-class1",
                "gil": "gil1"
            }
        }
    },
  '''

'''
 xconnect group PW-HE-TEST
  p2p pw-he-test1600
   interface PW-Ether1600
   neighbor ipv4 177.61.178.254 pw-id 1600
   !
  !
  p2p pw-he-test1700
   interface PW-Ether1700
   neighbor ipv4 177.61.178.254 pw-id 1700
   !
  !
  p2p pw-he-test1800
   interface PW-Ether1800
   neighbor ipv4 177.61.178.254 pw-id 1800
   !
  !
'''
context[XCONNECT+'_values'] = values
 
MSA_API.task_success('DONE: Insert workflow parameters into microservices', context, True)



