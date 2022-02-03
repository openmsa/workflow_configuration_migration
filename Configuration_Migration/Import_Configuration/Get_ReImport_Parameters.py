from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()


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


'''
if context.get('interfaces'):
  interfaces = context['interfaces']
  for interface in interfaces:
    if interface.get('source') and interface.get('dot1q') and interface.get('second_dot1q'):
      source        = interface['source']
      dot1q         = interface['dot1q']
      second_dot1q  = interface['second_dot1q']


'''     
        
MSA_API.task_success('DONE', context, True)
print(ret)
