from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()

#dev_var.add('real_or_simul_device')
#dev_var.add('source_device_id')
#dev_var.add('source_simul_device_id')
#dev_var.add('destination_simul_device_id')

dev_var.add('interfaces.0.source')
dev_var.add('interfaces.0.destination')
dev_var.add('interfaces.0.xconnect_group')
dev_var.add('interfaces.0.dot1q')
dev_var.add('interfaces.0.second_dot1q')
dev_var.add('interfaces.0.pseudowire_id')
dev_var.add('interfaces.0.pseudowire_ip')
dev_var.add('interfaces.0.pseudowire_class')
dev_var.add('interfaces.0.gil')

dev_var.add('enable_filter')

context = Variables.task_call(dev_var)
    
MSA_API.task_success('DONE', context, True)
print(ret)
