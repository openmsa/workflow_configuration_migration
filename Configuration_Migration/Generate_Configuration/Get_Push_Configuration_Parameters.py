from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()
dev_var.add('destination_device_id')
dev_var.add('push_to_device')

context = Variables.task_call(dev_var)

push_to_device = context['push_to_device']


MSA_API.task_success('DONE', context, True)
print(ret)
