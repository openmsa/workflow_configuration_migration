import os
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()

context = Variables.task_call(dev_var)

#get device_id from context
context['source_device_id_full'] = context['source_device_id']

MSA_API.task_success('DONE: set source real device to '+context['source_device_id_full'], context, True)



