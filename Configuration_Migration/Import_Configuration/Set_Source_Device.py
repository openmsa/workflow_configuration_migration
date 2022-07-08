import os
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()

context = Variables.task_call(dev_var)

if not context.get('real_source_and_real_destination'):
  context['real_source_and_real_destination'] = "false"
if context['real_source_and_real_destination'] == "true" or  context['real_source_and_real_destination'] == True:
  context['real_device_source'] = "true"
  context['push_to_device']     = "true"


if not context.get('real_device_source'):
  context['real_device_source'] = "false"
  
if context['real_device_source'] == "true" or  context['real_device_source'] == True:
  #Set Real ource device
  context['source_device_id_full'] = context['source_device_id']
  message= 'real'  #Set source simulated device
else:
  context['source_device_id_full'] = context['source_simul_device_id']
  message= 'simulated'



MSA_API.task_success('DONE: set '+message+' source device ('+context['source_device_id_full']+')', context, True)


