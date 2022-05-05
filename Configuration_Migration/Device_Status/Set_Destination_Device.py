import os
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()

context = Variables.task_call(dev_var)


if not context.get('real_device_source'):
  context['real_device_source'] = "false"
  
if context['real_device_source'] == "true" or  context['real_device_source'] == True:
  #Set Real ource device
  context['destination_device_id_full'] = context['destination_device_id']
  message= 'real'  #Set destination simulated device
  context['destination_device_type'] = ''
  
else:
  context['destination_device_id_full'] = context['destination_simul_device_id']
  message= 'simulated'
  context['destination_device_type'] = 'Simulated'


MSA_API.task_success('DONE: set '+message+' destination device ('+context['destination_device_id_full']+')', context, True)


