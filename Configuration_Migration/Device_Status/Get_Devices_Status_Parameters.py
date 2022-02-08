import json
import typing
import os
from pathlib import Path
from msa_sdk import constants
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from datetime import datetime


dev_var = Variables()

dev_var.add('source_device_id')

context = Variables.task_call(dev_var)

MSA_API.task_success('DONE', context, True)
print(ret)