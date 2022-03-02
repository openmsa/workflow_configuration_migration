from msa_sdk import util
from datetime import datetime
import time
import json
import requests

def create_event(device_id, severity, type_id, subtenant_ref, subtenant_id, message):
	username='superuser'
	password='x^ZyuGM6~u=+fY2G'
	dateTimeObj = datetime.now()
	format = "%Y-%m-%dT%H:%M:%S+0000"
	time1 = dateTimeObj.strftime(format)
	format = "%Y-%m-%d"
	date = dateTimeObj.strftime(format)
	timestamp = datetime.timestamp(dateTimeObj)
	url = "http://msa_es:9200/ubilogs-"+date+"/_doc"
	#util.log_to_process_file(process_id, url)
	payload = {"rawlog": ""+message+"", "device_id": ""+device_id+"", "timestamp": ""+str(timestamp)+"", "date": ""+time1+"", "customer_ref": ""+subtenant_ref+"", "customer_id": ""+subtenant_id+"", "severity": ""+severity+"", "type": ""+type_id+"", "subtype": "WF"}
	#util.log_to_process_file(process_id, payload)
	headers = {'content-type': 'application/json'}
	result = requests.post(url, auth=(username, password), json=payload, headers=headers)
	
	return result
