import json
import typing
import os
from pathlib import Path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.conf_profile import ConfProfile
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
dev_var = Variables()

dev_var = Variables()
dev_var.add('interfaces.0.source' )
dev_var.add('interfaces.0.destination' )
dev_var.add('interfaces.0.xconnect_group' )
dev_var.add('interfaces.0.pseudowire_id' )
dev_var.add('interfaces.0.pseudowire_class' )
dev_var.add('interfaces.0.gil' )


context = Variables.task_call(dev_var)

timeout = 600

    
MSA_API.task_success('TO DO'+context['source_device_id'] , context, True)



