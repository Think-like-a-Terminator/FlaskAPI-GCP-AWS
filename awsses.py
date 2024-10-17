import boto3
from botocore.exceptions import ClientError
import logging
from pprint import pprint
import re
import json



logger = logging.getLogger(__name__)


# for AWS SES Email templates tags
# Defines template tags, which are enclosed in two curly braces, such as {{tag}}.
TEMPLATE_REGEX = r"(?<={{).+?(?=}})"


class SesTemplate:
	"""Encapsulates Amazon SES template functions."""

	def __init__(self, ses_client):
		"""
		:param ses_client: A Boto3 Amazon SES client.
		"""
		self.ses_client = ses_client
		self.template = None
		self.template_tags = set()


	def _extract_tags(self, subject, text, html):
		"""
		Extracts tags from a template as a set of unique values.

		:param subject: The subject of the email.
		:param text: The text version of the email.
		:param html: The html version of the email.
		"""
		self.template_tags = set(re.findall(TEMPLATE_REGEX, subject + text + html))
		logger.info("Extracted template tags: %s", self.template_tags)


	def verify_tags(self, template_data):
		"""
		Verifies that the tags in the template data are part of the template.

		:param template_data: Template data formed of key-value pairs of tags and
							  replacement text.
		:return: True when all of the tags in the template data are usable with the
				 template; otherwise, False.
		"""
		diff = set(template_data) - self.template_tags
		if diff:
			logger.warning(
				"Template data contains tags that aren't in the template: %s", diff
			)
			return False
		else:
			return True


	def name(self):
		"""
		:return: Gets the name of the template, if a template has been loaded.
		"""
		return self.template["TemplateName"] if self.template is not None else None


	def create_template(self, name, subject, text, html):
		"""
		Creates an email template.

		:param name: The name of the template.
		:param subject: The subject of the email.
		:param text: The plain text version of the email.
		:param html: The HTML version of the email.
		"""
		try:
			template = {
				"TemplateName": name,
				"SubjectPart": subject,
				"TextPart": text,
				"HtmlPart": html,
			}
			response = self.ses_client.create_template(Template=template)
			logger.info("Created template %s.", name)
			self.template = template
			self._extract_tags(subject, text, html)
			return response
		except ClientError as e:
			logger.exception("Couldn't create template %s.", name)
			return e


	def delete_template(self, name):
		"""
		Deletes an email template.
		"""
		try:
			response = self.ses_client.delete_template(TemplateName=name)
			logger.info("Deleted template %s.", name)
			self.template = None
			self.template_tags = None
			return response
		except ClientError:
			logger.exception(
				"Couldn't delete template %s.", self.template["TemplateName"]
			)
			raise


	def get_template(self, name):
		"""
		Gets a previously created email template.

		:param name: The name of the template to retrieve.
		:return: The retrieved email template.
		"""
		try:
			response = self.ses_client.get_template(TemplateName=name)
			self.template = response["Template"]
			logger.info("Got template %s.", name)
			self._extract_tags(
				self.template["SubjectPart"],
				self.template["TextPart"],
				self.template["HtmlPart"],
			)
		except ClientError:
			logger.exception("Couldn't get template %s.", name)
			raise
		else:
			return self.template


	def list_templates(self):
		"""
		Gets a list of all email templates for the current account.

		:return: The list of retrieved email templates.
		"""
		try:
			response = self.ses_client.list_templates()
			templates = response["TemplatesMetadata"]
			return templates
			# logger.info("Got %s templates.", len(templates))
		except ClientError:
			return templates


	def update_template(self, name, subject, text, html):
		"""
		Updates a previously created email template.

		:param name: The name of the template.
		:param subject: The subject of the email.
		:param text: The plain text version of the email.
		:param html: The HTML version of the email.
		"""
		try:
			template = {
				"TemplateName": name,
				"SubjectPart": subject,
				"TextPart": text,
				"HtmlPart": html,
			}
			response = self.ses_client.update_template(Template=template)
			logger.info("Updated template %s.", name)
			self.template = template
			self._extract_tags(subject, text, html)
			return response
		except ClientError:
			logger.exception("Couldn't update template %s.", name)
			raise



class SesDestination:
	"""Contains data about an email destination."""

	def __init__(self, tos, ccs=None, bccs=None):
		"""
		:param tos: The list of recipients on the 'To:' line.
		:param ccs: The list of recipients on the 'CC:' line.
		:param bccs: The list of recipients on the 'BCC:' line.
		"""
		self.tos = tos
		self.ccs = ccs
		self.bccs = bccs

	def to_service_format(self):
		"""
		:return: The destination data in the format expected by Amazon SES.
		"""
		svc_format = {"ToAddresses": self.tos}
		if self.ccs is not None:
			svc_format["CcAddresses"] = self.ccs
		if self.bccs is not None:
			svc_format["BccAddresses"] = self.bccs
		return svc_format



class SesMailSender:
	"""Encapsulates functions to send emails with Amazon SES."""

	def __init__(self, ses_client):
		"""
		:param ses_client: A Boto3 Amazon SES client.
		"""
		self.ses_client = ses_client


	def send_email(self, source, destination, subject, text, html, reply_tos=None):
		"""
		Sends an email.

		Note: If your account is in the Amazon SES  sandbox, the source and
		destination email accounts must both be verified.

		:param source: The source email account.
		:param destination: The destination email account.
		:param subject: The subject of the email.
		:param text: The plain text version of the body of the email.
		:param html: The HTML version of the body of the email.
		:param reply_tos: Email accounts that will receive a reply if the recipient
						  replies to the message.
		:return: The ID of the message, assigned by Amazon SES.
		"""
		send_args = {
			"Source": source,
			"Destination": destination.to_service_format(),
			"Message": {
				"Subject": {"Data": subject},
				"Body": {"Text": {"Data": text}, "Html": {"Data": html}},
			},
		}
		if reply_tos is not None:
			send_args["ReplyToAddresses"] = reply_tos
		try:
			response = self.ses_client.send_email(**send_args)
			message_id = response["MessageId"]
			logger.info(
				"Sent mail %s from %s to %s.", message_id, source, destination.tos
			)
		except ClientError:
			logger.exception(
				"Couldn't send mail from %s to %s.", source, destination.tos
			)
			raise
		else:
			return message_id


	def send_templated_email(
		self, source, destination, template_name, template_data, reply_tos=None
	):
		"""
		Sends an email based on a template. A template contains replaceable tags
		each enclosed in two curly braces, such as {{name}}. The template data passed
		in this function contains key-value pairs that define the values to insert
		in place of the template tags.

		Note: If your account is in the Amazon SES  sandbox, the source and
		destination email accounts must both be verified.

		:param source: The source email account.
		:param destination: The destination email account.
		:param template_name: The name of a previously created template.
		:param template_data: JSON-formatted key-value pairs of replacement values
							  that are inserted in the template before it is sent.
		:return: The ID of the message, assigned by Amazon SES.
		"""
		
		sesdestination = {"ToAddresses": destination}

		send_args = {
			"Source": source,
			"Destination": sesdestination,
			"Template": template_name,
			"TemplateData": json.dumps(template_data),
		}
		if reply_tos is not None:
			send_args["ReplyToAddresses"] = reply_tos
		try:
			response = self.ses_client.send_templated_email(**send_args)
			message_id = response["MessageId"]
			print(response)
			logger.info(
				"Sent templated mail %s from %s to %s.",
				message_id,
				source,
				destination,
			)
		except ClientError:
			print("Couldn't send templated email from %s to %s.", source, destination)
			logger.exception(
				"Couldn't send templated mail from %s to %s.", source, destination
			)
			raise
		else:
			return message_id