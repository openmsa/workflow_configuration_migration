from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()

#dev_var.add('generate_file')

context = Variables.task_call(dev_var)

MSA_API.task_success('DONE', context, True)
print(ret)
