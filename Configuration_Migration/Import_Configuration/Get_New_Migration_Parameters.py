import requests
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API

dev_var = Variables()

dev_var.add('source_device_id')
dev_var.add('source_simul_device_id')
dev_var.add('destination_device_id')
dev_var.add('destination_simul_device_id')

dev_var.add('customer_id')

dev_var.add('batch_load')
dev_var.add('interface_list')


dev_var.add('interfaces.0.source')
dev_var.add('interfaces.0.destination')
dev_var.add('interfaces.0.dot1q')
dev_var.add('interfaces.0.second_dot1q')
dev_var.add('interfaces.0.xconnect_group')
dev_var.add('interfaces.0.pseudowire_class')
dev_var.add('interfaces.0.p2p')
#HairPin
dev_var.add('interfaces.0.hairpin')
dev_var.add('interfaces.0.pwid')
dev_var.add('interfaces.0.hl4_vendor')
dev_var.add('interfaces.0.hl4_name')
dev_var.add('interfaces.0.hl4_ip')


dev_var.add('data_filter')
dev_var.add('enable_filter')
dev_var.add('real_source_and_real_destination')
dev_var.add('real_device_source')


context = Variables.task_call(dev_var)

context['customer_id_instance_id'] =  context['customer_id'] + '_#' +context['SERVICEINSTANCEID']


#When the interfaces contains 'dot1q' and 'second_dot1q' we add it into the interface name
if not context['batch_load'] :
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
else:
    #interfacesMapFile = requests.get(context['batchloadfile'])
    #textString = interfacesMapFile.text
    textString = context['interface_list'];
    interfacesMap = textString.replace("\r\n","\n").split('\n')
    new_interfaces = []
    for item in interfacesMap:
        itemArray = item.split(';')
        if len(itemArray) == 12: 
            interface = {}
            interface['source'] = itemArray[0]
            interface['destination'] = itemArray[1]
            interface['dot1q'] = itemArray[2]
            interface['second_dot1q'] = itemArray[3]
            interface['xconnect_group'] = itemArray[4]
            interface['pseudowire_class'] = itemArray[5]
            interface['p2p'] = itemArray[6]
            interface['hairpin'] = itemArray[7]
            interface['pwid'] = itemArray[8]
            interface['hl4_vendor'] = itemArray[9]
            interface['hl4_name'] = itemArray[10]
            interface['hl4_ip'] = itemArray[11]

            new_interfaces.append(interface)
    context['interfaces'] = new_interfaces

MSA_API.task_success('DONE: user parameters OK', context, True)