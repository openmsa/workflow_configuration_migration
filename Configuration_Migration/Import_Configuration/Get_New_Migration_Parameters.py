from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()

dev_var.add('source_simul_device_id')
dev_var.add('destination_simul_device_id')

dev_var.add('customer_id')

dev_var.add('interfaces.0.source')
dev_var.add('interfaces.0.destination')
dev_var.add('interfaces.0.xconnect_group')
dev_var.add('interfaces.0.dot1q')
dev_var.add('interfaces.0.second_dot1q')
dev_var.add('interfaces.0.pseudowire_id')
dev_var.add('interfaces.0.pseudowire_ip')
dev_var.add('interfaces.0.pseudowire_class')
dev_var.add('interfaces.0.gil')

dev_var.add('data_filter')
dev_var.add('enable_filter')

#dev_var.add('generate_file')
dev_var.add('link.0.MicroService')
dev_var.add('link.0.file_link')

context = Variables.task_call(dev_var)


#When the interfaces contains 'dot1q' and 'second_dot1q' we add it into the interface name
if context.get('interfaces'):
  new_interfaces = []
  interfaces = context['interfaces']
  for interface in interfaces:
    if interface.get('destination') and interface.get('dot1q') and interface.get('second_dot1q'):
      destination  = interface['destination']
      dot1q        = interface['dot1q']
      second_dot1q = interface['second_dot1q']
      if dot1q and second_dot1q and not destination.endswith('.'+dot1q+second_dot1q):
        interface['destination'] = destination+'.'+dot1q+second_dot1q 
        context['change interface destination '+destination+ ' to'] = destination+'.'+dot1q+second_dot1q 
  
    new_interfaces.append(interface)
    
  context['interfaces'] = new_interfaces    
    

MSA_API.task_success('DONE', context, True)
print(ret)
