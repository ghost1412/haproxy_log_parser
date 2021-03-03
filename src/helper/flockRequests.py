import json
import traceback
from datetime import datetime
import requests
import sys

info_report_url = ""

# debug_report flock url
debug_report_url = ""

# error report flock url
error_report_url = ""

# printing exception info
def exception_info(report=True):
	exc_type, exc_value, exc_tb = sys.exc_info()
	print("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
	if report:
		error_report("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

# debug report function to send msg to flock url
def debug_report(message):

	data = {"text": message}
	headers = {"Content-Type": "application/json"}
	try:
		requests.post(debug_report_url, data=json.dumps(data), headers=headers)
	except requests.exceptions.RequestException as e:
		# writing the message to the file 
		with open('record_offline','a+') as f:
			f.write(datetime.utcnow().strftime("%I:%M%p on %B %d, %Y") + " " + message)
	
		exception_info(report=False)
		print("Could not send alert on flock!")

# error report function to send msg to flock url
def error_report(message):

	data = {"text": message}
	headers = {"Content-Type": "application/json"}
	try:
		requests.post(error_report_url, data=json.dumps(data), headers=headers)
	except requests.exceptions.RequestException as e:
		# writing the message to the file 
		with open('record_offline','a+') as f:
			f.write(datetime.utcnow().strftime("%I:%M%p on %B %d, %Y") + " " + message)
	
		exception_info(report=False)
		print("Could not send alert on flock!")


# info function to send info msg to flock channel
def info_report(message):
	data = {"text": message}
	headers = {"Content-Type": "application/json"}
	try:
		requests.post(info_report_url, data=json.dumps(data), headers=headers)
	except requests.exceptions.RequestException as e:
		# writing the message to the file 
		with open('record_offline','a+') as f:
			f.write(datetime.utcnow().strftime("%I:%M%p on %B %d, %Y") + " " + message)

		exception_info(report=False)
		print("Could not send alert on flock!")
