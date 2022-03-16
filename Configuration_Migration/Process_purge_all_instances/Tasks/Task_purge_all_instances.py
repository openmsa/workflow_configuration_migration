'''
This script is used to puerge all instances for this WF
'''
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk.orchestration import Orchestration
from msa_sdk.variables import Variables
from datetime import datetime
from msa_sdk import constants
import re
import json
import sys
import time

dev_var = Variables()
context = Variables.task_call(dev_var)

context['customer_id_instance_id'] =  'No_customer_#' +context['SERVICEINSTANCEID']


Orchestration = Orchestration(context['UBIQUBEID'])
response = Orchestration.list_service_instances()
service_list = json.loads(Orchestration.content)
context['all_services'] = service_list

for service in service_list:
  if service['state'] == 'ACTIVE':
    if service['name'] in ('Process/Workflows/Convert_YANG_To_XML/Convert_YANG_To_XML', 'Process/workflow_configuration_migration/Configuration_Migration/Configuration_Migration'):
      is_finished = True
      response = Orchestration.list_process_instances_by_service(service['id'])
      for process in json.loads(Orchestration.content):
        if process['status']['status'] not in ('ENDED', 'FAILED', 'FAIL'):
          is_finished = False
          #context['status_'+str(service['id'])]= process
          
      if is_finished:
        Orchestration.delete_service(service['id'])      
    
#Finish the task correctlly
result = MSA_API.process_content('ENDED', 'All old previous instacnes cleaned' , context, True)
print(result)
