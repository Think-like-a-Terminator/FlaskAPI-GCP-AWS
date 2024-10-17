from flask import Flask, request
from flask_restful import Api, Resource
import base64
from flask_cors import CORS
from google.oauth2 import service_account
from google.cloud import datastore, storage
from google.api_core.exceptions import Conflict
import boto3
from botocore.exceptions import ClientError
import json
from datetime import timedelta
# importing SES classes from awsses.py file
from awsses import SesTemplate
from awsses import SesMailSender

# python 3.11 (API can also work with python 3.7+) 


app = Flask(__name__)
CORS(app)
api = Api(app)


# api keys for API Authentication (BASIC AUTH)
with open('api_keys.json', encoding='utf8') as json_data:
	users = json.load(json_data)


def check_auth(username, password):
	"""Check if a username / password combination is valid."""
	return users.get(username) == password


# Google Cloud Platform Service Account Credentials
credentials = service_account.Credentials.from_service_account_file(
		'INSERT GCP SERVICE ACCOUNT CREDS JSON FILE')

datastore_client = datastore.Client(credentials=credentials)

storage_client = storage.Client(credentials=credentials)


# AWS SES Credentials
with open('INSERT AWS SES CREDS FILE', 'r') as f:
	smtp_credentials = f.readlines()
smtp_credentials = smtp_credentials[1].split(',')
# smtp_credentials[0] is the SMTP user name which we don't need
AWS_ACCESS_KEY_ID = str(smtp_credentials[1]).strip()
AWS_SECRET_ACCESS_KEY = str(smtp_credentials[2]).strip()
f.close()

AWS_REGION = "us-west-2"
ses_client = boto3.client('ses',
						  region_name=AWS_REGION, 
						  aws_access_key_id=AWS_ACCESS_KEY_ID, 
						  aws_secret_access_key=AWS_SECRET_ACCESS_KEY
						  )

sesTemplate = SesTemplate(ses_client)
sesMailSender = SesMailSender(ses_client)



def create_template(template_name, subject, text_part, html_part):
	TEMPLATE_NAME = template_name
	SUBJECT = subject
	TEXT_PART = text_part
	HTML_PART = html_part
	# Try to create the template.
	try:
		#Provide the contents of the email.
		response = sesTemplate.create_template(
			name=TEMPLATE_NAME, subject=SUBJECT, text=TEXT_PART, html=HTML_PART)
		print(response)
		if 'An error occurred (AlreadyExists)' in str(response):
			return {'status': 'error', 'error': 'Template already exists'}
		else:
			return {'status': 'success', 'response': response }
	# Display an error if something goes wrong.	
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {'status': 'error', 'error': e.response['Error']['Message'] }
	

def delete_template(template_name):
	TEMPLATE_NAME = template_name
	# Try to delete the template.
	try:
		#Provide the contents of the email.
		response = sesTemplate.delete_template(
			TEMPLATE_NAME)
		print("Template deleted! Message ID:"), print(response)
		return {'status': 'success', 'response': response }
	# Display an error if something goes wrong.	
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {'status': 'error', 'error': e.response['Error']['Message'] }
	

def get_template(template_name):
	TEMPLATE_NAME = template_name
	# Try to get the template.
	try:
		#Provide the contents of the email.
		response = sesTemplate.get_template(
			TEMPLATE_NAME)
		print("Template retrieved! Message ID:"), print(response)
		return response
	# Display an error if something goes wrong.	
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {'status': 'error', 'error': e.response['Error']['Message'] }
	

def update_template(template_name, subject, text_part, html_part):
	TEMPLATE_NAME = template_name
	SUBJECT = subject
	TEXT_PART = text_part
	HTML_PART = html_part
	# Try to update the template.
	try:
		#Provide the contents of the email.
		response = sesTemplate.update_template(
			name=TEMPLATE_NAME, subject=SUBJECT, text=TEXT_PART, html=HTML_PART)
		print("Template updated! Response:"), print(response)
		return {'status': 'success', 'response': response }
	# Display an error if something goes wrong.	
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {'status': 'error', 'error': e.response['Error']['Message'] }


def list_ses_templates():
	# no args neeeded as it will return all templates under our ses account
	# Try to list the templates.
	try:
		#Provide the contents of the email.
		response = sesTemplate.list_templates()
		print("Templates listed! Response:"), print(str(response))
		return str(response)
	# Display an error if something goes wrong.	
	except ClientError as e:
		return str(response)
		# print(e.response['Error']['Message'])
		# return {'status': 'error', 'error': e.response['Error']['Message'] }
	

def send_template_email(sender, recipients, template_name, template_data, replytos=None):
	SOURCE = sender
	DESTINATION = recipients  # recipients is a list of email addresses
	TEMPLATE_NAME = template_name
	TEMPLATE_DATA = template_data
	REPLYTOS = replytos
	# Try to send the email.
	try:
		#Provide the contents of the email.
		response = sesMailSender.send_templated_email(
			source=SOURCE, destination=DESTINATION, template_name=TEMPLATE_NAME, template_data=TEMPLATE_DATA, reply_tos=REPLYTOS)
		print("Template Email sent! Message ID:"), print(response)
		return {'status': 'success', 'response': response }
	# Display an error if something goes wrong.	
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {'status': 'error', 'error': e.response['Error']['Message'] }


# one time email send without a template
def send_email(sender, recipients, subject, body_html, body_text):
	SENDER = sender
	RECIPIENTS = recipients  # recipients is a list of email addresses
	AWS_REGION = "us-west-2"
	SUBJECT = subject
	BODY_HTML = body_html   
	# The email body for recipients with non-HTML email clients.
	BODY_TEXT = body_text
	# The character encoding for the email.
	CHARSET = "UTF-8"
	# Try to send the email.
	try:
		#Provide the contents of the email.
		response = ses_client.send_email(
			Destination={
				'ToAddresses': 
					RECIPIENTS
			},
			Message={
				'Body': {
					'Html': {
						'Charset': CHARSET,
						'Data': BODY_HTML,
					},
					'Text': {
						'Charset': CHARSET,
						'Data': BODY_TEXT,
					},
				},
				'Subject': {
					'Charset': CHARSET,
					'Data': SUBJECT,
				},
			},
			Source=SENDER,
		)
		print("Email sent! Reponse:"),
		print(response)
		return {'status': 'success', 'response': response }
	# Display an error if something goes wrong.	
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {'status': 'error', 'error': e.response['Error']['Message'] }



def read_data(kind_id, key_id=None, object_type=None, filters=None, sort=None):
	"""
			request: needs to be json format dictionary of key value pairs 
						and either key_id or object_type must be populated

			if key_id is provided, will query one specific key, i.e = "customer000000001",
			otherwise if object_type is provided, will query all objects = "customer" or 
			"case" or "nps", etc.

			{
				kind_id: "", (required)
				key_id: "", (optional)
				object_type: "", (optional)
				filters: {}, (optional)
				sort: {} (optional)
			}

			kind_id example: "client000000001"
			key_id example:  if updating specific customer then key_id = "customer000000001"
			object_type:  if querying all objects related to Cases then object_type = "case"
			filters example:  json format dictionary of key value pairs
								{
									"filter1": {"filter_field": "priority", 
												"filter_op": "=",
												"filter_value": "High"},
									"filter2": {"filter_field": "created_date", 
												"filter_op": ">=",
												"filter_value": "2023-04-01"},
								}
			sort example:  json format dictionary of key value pairs
							only 1 sort allowed due to bug in datastore
									{
										"sort_direction": "asc",
										"sort_value": "due_date"
									},
	"""
	query = datastore_client.query(kind=kind_id)
	if key_id != None:
		query = datastore_client.query(kind=kind_id)
		first_key = datastore_client.key(kind_id, key_id)
		query.key_filter(first_key, "=")
	elif object_type != None:
		query = datastore_client.query(kind=kind_id)
		query.add_filter("object_type", "=", object_type)
	if filters != None:  # filters is python dict with values being nested dicts so must iterate over filters.values() 
		for items in filters.values():   # and use items["filter_field"] to retrieve values inside nested dicts
			filter_field = items["filter_field"]
			filter_op = items["filter_op"]
			filter_value = items["filter_value"]
			print(filter_field)
			print(filter_op)
			print(filter_value)
			query.add_filter(filter_field, filter_op, filter_value)
	if sort != None:
		sort_direction = sort["sort_direction"]
		sort_value = sort["sort_value"]
		if sort_direction == "desc":
				sort_string = "-" + str(sort_value)
				query.order = [sort_string]
		else:
			query.order = [sort_value]
	results = list(query.fetch())
	if not results:
		return "No result is returned"
	else:
		data_list = []
		for index in range(len(results)):
			d = dict(results[index])
			if results[index].key.id == None:
				d["key_id"] = results[index].key.name
			else:
				d["key_id"] = results[index].key.id
			data_list.append(d)
		return data_list


def update_data(kind_id, key_id, data):
	"""
		args:
			kind_id:  name/ID of the kind 'ClientID', example: "client000000001", (client000000001, client000000002, etc. it would be the ID's of customers)
			key_id:  name/ID of the key you want to update. Essentially, what object you want to update
			   			example:  update customer then key_id = "customer000000001" 
									or update case then key_id = "case000000001" 
			data:  needs to be json format dictionary of values, the data would be the key value pairs of fields "customers", "nps", "surveys", etc.
	"""
	with datastore_client.transaction():
		complete_key = datastore_client.key(kind_id, key_id)
		task = datastore_client.get(complete_key)
		for prop in task:
			task[prop] = task[prop]
		for items in data:
			task[items] = data[items]
		datastore_client.put(task)


def create_data(kind_id, data, key_id=None):
	"""
		args:
			kind_id:  name/ID of the kind 'ClientID', example: "client000000001", (client000000001, client000000002, etc. it would be the ID's of this CRM's customers)
			key_id:  name/ID of the key you want to update. Essentially, what object you want to update
			   			example:  update customer then key_id = "customer000000001" 
							  		or update cta then key_id = "cta000000001"
									or update case then key_id = "case000000001" 
			data:  needs to be json format dictionary of values, the data would be the key value pairs of fields "customers", "nps", "surveys", etc.
	"""
	if key_id == None:
		# if key_id is None, then it will auto generate a key_id
		complete_key = datastore_client.key(kind_id)
		task = datastore.Entity(key=complete_key)
		task.update(data)
		datastore_client.put(task)
	else:
		complete_key = datastore_client.key(kind_id, key_id)
		task = datastore.Entity(key=complete_key)
		# CREATING OBJECT (even though the function is called update, it is creating an object)
		task.update(data)
		datastore_client.put(task)


def delete_data(kind_id, key_id, entity_property=None):
	if entity_property != None:
		with datastore_client.transaction():
			key = datastore_client.key(kind_id, key_id)
			task = datastore_client.get(key)
			if entity_property in task:
				del task[entity_property]
				datastore_client.put(task)
	else:
		key = datastore_client.key(kind_id, key_id)
		datastore_client.delete(key)


class ReadData(Resource):
	def post(self):
		"""
			{
			kind_id: "", (required)
			key_id: "", (optional)
			object_type: "", (optional)
			filters: {}, (optional)
			sort: {} (optional)
			}

			filters example:  json format dictionary of key value pairs with filters inside nested dict
						{
							"filter1": {"filter_field": "priority", 
										"filter_op": "=",
										"filter_value": "High"},
							"filter2": {"filter_field": "created_date", 
										"filter_op": ">=",
										"filter_value": "2023-04-01"},
						}
			sort example:  json format dictionary of key value pairs, NO nested dict
							only 1 sort allowed due to bug in datastore
									{
										"sort_direction": "asc",
										"sort_value": "due_date"
									},
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			query_data = request.get_json()
			kind_id = query_data["kind_id"]
			if "key_id" in query_data.keys():
				key_id_criteria = query_data["key_id"]
				if ("filters" not in query_data.keys()) and ("sort" not in query_data.keys()):
					retrieved_data = read_data(kind_id=kind_id, key_id=key_id_criteria)
				elif ("filters" in query_data.keys()) and ("sort" not in query_data.keys()):
					filters_criteria = query_data["filters"]
					retrieved_data = read_data(kind_id=kind_id, key_id=key_id_criteria, filters=filters_criteria)
				elif ("filters" not in query_data.keys()) and ("sort" in query_data.keys()):
					sort_criteria = query_data["sort"]
					retrieved_data = read_data(kind_id=kind_id, key_id=key_id_criteria, sort=sort_criteria)
				elif ("filters" in query_data.keys()) and ("sort" in query_data.keys()):
					filters_criteria = query_data["filters"]
					sort_criteria = query_data["sort"]
					retrieved_data = read_data(kind_id=kind_id, key_id=key_id_criteria, filters=filters_criteria, sort=sort_criteria)
			elif "object_type" in query_data.keys():
				object_type_criteria = query_data["object_type"]
				if ("filters" not in query_data.keys()) and ("sort" not in query_data.keys()):
					retrieved_data = read_data(kind_id=kind_id, object_type=object_type_criteria)
				elif ("filters" in query_data.keys()) and ("sort" not in query_data.keys()):
					filters_criteria = query_data["filters"]
					retrieved_data = read_data(kind_id=kind_id, object_type=object_type_criteria, filters=filters_criteria)
				elif ("filters" not in query_data.keys()) and ("sort" in query_data.keys()):
					sort_criteria = query_data["sort"]
					retrieved_data = read_data(kind_id=kind_id, object_type=object_type_criteria, sort=sort_criteria)
				elif ("filters" in query_data.keys()) and ("sort" in query_data.keys()):
					filters_criteria = query_data["filters"]
					sort_criteria = query_data["sort"]
					retrieved_data = read_data(kind_id=kind_id, object_type=object_type_criteria, filters=filters_criteria, sort=sort_criteria)
			else:
				if ("filters" in query_data.keys()) and ("sort" not in query_data.keys()):
					filters_criteria = query_data["filters"]
					retrieved_data = read_data(kind_id=kind_id, filters=filters_criteria)
				elif ("filters" in query_data.keys()) and ("sort" in query_data.keys()):
					filters_criteria = query_data["filters"]
					sort_criteria = query_data["sort"]
					retrieved_data = read_data(kind_id=kind_id, filters=filters_criteria, sort=sort_criteria)
			return {
				"retrieved_data": retrieved_data 
			}
		else:
			return {"message": "Authentication failed"}, 403


class UpdateData(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				kind_id: "", (required)
				key_id: "", (required)
				data: {}  (required)
			}

			kind_id example: "client000000001"
			key_id example:  if updating customer then key_id = "customer000000001"
			data example:  json format dictionary of key value pairs, examples above
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			update_request = request.get_json()
			kind_id = update_request["kind_id"]
			key_id = update_request["key_id"]
			updated_values = update_request["data"]
			update_data(kind_id=kind_id, key_id=key_id, data=updated_values)
			return {
				"status": "success",
				"updated_kind_id": kind_id,
				"updated_key_id": key_id,
				"updated_data": updated_values
			}
		else:
			return {"message": "Authentication failed"}, 403


class CreateData(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				kind_id: "" (required)
				key_id: "" (optional)
				data: {} (required)
			}

			kind_id example: "client000000001"
			key_id example:  if updating customer then key_id = "customer000000001"
			data example:  json format dictionary of key value pairs, examples above
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			create_request = request.get_json()
			kind_id = create_request["kind_id"]
			# check if key_id is provided, if not then it will auto generate a key_id
			if "key_id" not in create_request.keys():
				key_id = None
			else:
				key_id = create_request["key_id"]
			created_values = create_request["data"]
			create_data(kind_id=kind_id, key_id=key_id, data=created_values)
			return {
				"status": "success",
				"created_kind_id": kind_id,
				"created_key_id": key_id,
				"created_data": created_values
			}
		else:
			return {"message": "Authentication failed"}, 403


class DeleteData(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				kind_id: "",
				key_id: "",
				entity_property: "" (optional)
			}

			kind_id example: "client000000001"
			key_id example:  if updating customer then key_id = "customer000000001"
			entity_property example:  string, example: "cases_open"
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			delete_request = request.get_json()
			kind_id = delete_request["kind_id"]
			key_id = delete_request["key_id"]
			if ("entity_property" in delete_request.keys()):
				entity_property = delete_request["entity_property"]
				delete_data(kind_id=kind_id, key_id=key_id, entity_property=entity_property)
				return {
					"status": "success",
					"deleted_kind_id": kind_id,
					"deleted_key_id": key_id,
					"deleted_entity_property": entity_property
				}
			else:
				delete_data(kind_id=kind_id, key_id=key_id)
				return {
					"status": "success",
					"deleted_kind_id": kind_id,
					"deleted_key_id": key_id,
				}
		else:
			return {"message": "Authentication failed"}, 403


class SendEmailData(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				sender: "", (required)
				recipients: array, (required)
				subject: ""  (required)
				body_html: "" (required)
				body_text: "" (required)
			}
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			email_request = request.get_json()
			sender, recipients, subject, body_html, body_text = email_request["sender"], email_request["recipients"], email_request["subject"], email_request["body_html"], email_request["body_text"]
			# extract all the values from recipients and add it to a list
			recipients_list = []
			for recipient in recipients:
				recipients_list.append(recipient)
			results = send_email(sender=sender, recipients=recipients_list, subject=subject, body_html=body_html, body_text=body_text)
			return results
		else:
			return {"message": "Authentication failed"}, 403


class CreateTemplate(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				template_name: "", (required) (kind_id + '_' + templateName)
				subject: "", (required)
				html_part: "", (required)
				text_part: "" (required)
			}
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			template_request = request.get_json()
			templateName, subject, html_part, text_part = template_request["template_name"], template_request["subject"], template_request["html_part"], template_request["text_part"]
			results = create_template(template_name=templateName, subject=subject, html_part=html_part, text_part=text_part)
			return results
		else:
			return {"message": "Authentication failed"}, 403
	

class DeleteTemplate(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				template_name: "", (required) (kind_id + '_' + templateName)
			}
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			template_request = request.get_json()
			templateName = template_request["template_name"]
			results = delete_template(template_name=templateName)
			return results
		else:
			return {"message": "Authentication failed"}, 403
	

class GetTemplate(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				template_name: "", (required) (kind_id + '_' + templateName (spaces in templateName should be replaced with underscores))
			}
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			template_request = request.get_json() # transforms json request to python dictionary
			templateName = template_request["template_name"]
			results = get_template(template_name=templateName)
			return results
		else:
			return {"message": "Authentication failed"}, 403
	

class UpdateTemplate(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			{
				template_name: "", (required) (kind_id + '_' + templateName)
				subject: "", (required)
				html_part: "", (required)
				text_part: "" (required)
			}
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			template_request = request.get_json() # transforms json request to python dictionary
			templateName, subject, html_part, text_part = template_request["template_name"], template_request["subject"], template_request["html_part"], template_request["text_part"]
			results = update_template(template_name=templateName, subject=subject, html_part=html_part, text_part=text_part)
			return results
		else:
			return {"message": "Authentication failed"}, 403
	

class ListTemplates(Resource):
	
	def post(self):
		"""
			no args because it returns all templates under our ses account, each template is formatted with a specific kind_id + '_' + templateName
		"""
		# dummy_request = request.get_json() # might need to remoe error
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			results = list_ses_templates()
			return results
		else:
			return {"message": "Authentication failed"}, 403
	

class SendEmailTemplate(Resource):
	
	def post(self):
		"""
			request: needs to be json format dictionary of key value pairs

			sender, recipients, template_name, template_data
			{
				sender: "", (required)
				recipients: array, (required)
				template_name: "", (required) (templateName + '_' + kind_id)
				template_data: {} (required), (key value pairs of tags to replace in the template)
				replytos: array (optional)
			}
		"""
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			sendtemplate_request = request.get_json() # transforms json request to python dictionary
			sender, recipients, template_name, template_data = sendtemplate_request["sender"], sendtemplate_request["recipients"], sendtemplate_request["template_name"], sendtemplate_request["template_data"]
			if "replytos" in sendtemplate_request.keys():
				replytos = sendtemplate_request["replytos"]
				results = send_template_email(sender=sender, recipients=recipients, template_name=template_name, template_data=template_data, replytos=replytos)
			else:
				results = send_template_email(sender=sender, recipients=recipients, template_name=template_name, template_data=template_data, replytos=None)
			return results
		else:
			return {"message": "Authentication failed"}, 403
	

class CreateGcpBucket(Resource):
	def post(self):
		# Parse bucket name and location from the request
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			data = request.get_json()
			bucket_name = data.get('bucketName')
			location = data.get('location', 'US')
			try:
				bucket = storage_client.bucket(bucket_name)
				new_bucket = storage_client.create_bucket(bucket, location=location)
				# Set CORS configuration
				cors_configuration = [{
					"origin": ["http://localhost:3000", "http://localhost:5000", "https://example.com", "INSERT YOUR FRONTEND URL"],
					"responseHeader": ["Content-Type"],
					"method": ["PUT", "POST", "GET"],
					"maxAgeSeconds": 3600
				}]
				new_bucket.cors = cors_configuration
				new_bucket.patch()  # Update the bucket with the new CORS settings
				return {'message': f'Bucket {bucket_name} created.'}, 200
			except Conflict:
				return {'error': 'Bucket already exists'}, 409
			except Exception as e:
				return {'error': str(e)}, 500
		else:
			return {"message": "Authentication failed"}, 403


class GenerateSignedURL(Resource):
	# @cross_origin(origin='http://localhost:3000')
	def post(self):
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			object_folder_name = request.form['object_folder_name']
			object_folder_name = str(object_folder_name).lower().replace(' ', '_').replace('.', '')
			kind_id = request.form['kind_id']
			file_name = request.form['file_name']

			if not file_name or not object_folder_name or not kind_id:
				return {'error': 'Missing file_name or object_folder_name or kind_id or content_type'}, 400

			# Corrected bucket name and object name
			bucket_name = kind_id  # Assuming kind_id is your bucket name
			object_name = f'{object_folder_name}/{file_name}'  # Creating a folder-like structure within the bucket

			bucket = storage_client.bucket(bucket_name)
			blob = bucket.blob(object_name)

			# Generate a signed URL for the file upload
			url = blob.generate_signed_url(
				version='v4',
				expiration=timedelta(minutes=45),  # URL expires in 45 minutes
				method='PUT',
			)

			print('Generated signed URL: {}'.format(url))

			return {'url': url}, 200


class ListFilesfromGcpBucket(Resource):
	def post(self):
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			data = request.get_json()
			bucket_name = data.get('bucketName')
			folder_name = data.get('folderName', '')
			# Ensure the folder name (prefix) ends with a slash
			if folder_name and not folder_name.endswith('/'):
				folder_name += '/'
			bucket = storage_client.bucket(bucket_name)
			# List blobs with the given folder name as a prefix
			files = bucket.list_blobs(prefix=folder_name)
			file_names = [file.name for file in files]
			return file_names, 200
		else:
			return {"message": "Authentication failed"}, 403


class DownloadUrlfromGcpBucket(Resource):
	# @cross_origin(origin='http://localhost:3000')
	def post(self):
		auth = request.headers.get('Authorization')
		if not auth:
			return {"message": "Missing authorization header"}, 401
		encoded_credentials = auth.split(' ')[1]
		decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
		username, password = decoded_credentials.split(':')
		if check_auth(username, password):
			data = request.get_json()
			file_name = data.get('fileName') # fileName from request is actual folder path + file name (only for download is fileName the folder path + file name)
			bucket_name = data.get('bucketName')
			try:
				bucket = storage_client.bucket(bucket_name)
				blob = bucket.blob(file_name)
				# Generate a signed URL for the file download
				downloadUrl = blob.generate_signed_url(
					version='v4',
					expiration=timedelta(minutes=15),  # URL expires in 15 minutes
					method='GET'
				)
				return {'url': downloadUrl}
			except Exception as e:
				return {'error': str(e)}, 500
		else:
			return {"message": "Authentication failed"}, 403



api.add_resource(ReadData, "/api/v1/read")
api.add_resource(UpdateData, "/api/v1/update")
api.add_resource(CreateData, "/api/v1/create")
api.add_resource(DeleteData, "/api/v1/delete")
api.add_resource(SendEmailData, "/api/v1/sendemail")
api.add_resource(SendEmailTemplate, "/api/v1/sendemailtemplate")
api.add_resource(CreateTemplate, "/api/v1/createtemplate")
api.add_resource(DeleteTemplate, "/api/v1/deletetemplate")
api.add_resource(GetTemplate, "/api/v1/gettemplate")
api.add_resource(UpdateTemplate, "/api/v1/updatetemplate")
api.add_resource(ListTemplates, "/api/v1/listtemplates")
api.add_resource(CreateGcpBucket, "/api/v1/createbucket")
api.add_resource(GenerateSignedURL, "/api/v1/getsignedurl")
api.add_resource(DownloadUrlfromGcpBucket, "/api/v1/getdownloadurlfrombucket")
api.add_resource(ListFilesfromGcpBucket, "/api/v1/listfilesfrombucket")


if __name__ == '__main__':
	app.run()
