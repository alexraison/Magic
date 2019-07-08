from app.slackApiChannel import Channel
import requests
import json
import os
import datetime

class slack_bot:

	def __init__(self, channel_id, bot_name, bot_icon, live=True):
		self.token = os.environ['SLACK_TOKEN']
		self.default_message = {
		'token': self.token,
		'channel': channel_id,
		'username': bot_name,
		'icon_url': bot_icon,
		'link_names':"1"
		}
		self.live = live
		self.session = requests.session()

	def post_message(self, message_text):
		message = self.default_message.copy()
		message['text'] = message_text
		self._send_or_simulate(message, 'simulating post of message: {!s}'.format(message_text))

	def post_images(self, image_urls_array, pretext="", fallback="Couldn't display image"):
		if len(image_urls_array) == 0:
			return
		message = self.default_message.copy()
		message['attachments'] = []
		attachment_count = 0
		for image_url in image_urls_array:
			if attachment_count == 0:
				attachment = {
				'image_url': image_url,
				'pretext': pretext,
				'fallback': fallback,
				'color': '#764FA5'
				}
			else:
				attachment = {
				'image_url': image_url,
				'fallback': fallback
				}
			message['attachments'].append(attachment)
			attachment_count += 1
		message['attachments'] = json.dumps([attachment])
		self._send_or_simulate(message, 'simulating post of images: {!s}'.format(str(image_urls_array)))

	def post_multiline_message(self, message_text):
		message = self.default_message.copy()
		attachment = {
		'text': message_text
		}
		message['attachments'] = json.dumps([attachment])
		self._send_or_simulate(message, 'simulating post of multi-line message: {!s}'.format(message_text))

	def post_attachment(self, attachment):
		message = self.default_message.copy()
		attachment = attachment
		message['attachments'] = json.dumps([attachment])
		self._send_or_simulate(message, 'simulating post of multi-line message')

	def _send_or_simulate(self, payload, simulate_text):
		if self.live:
			print(payload)
			response = self.session.post("https://slack.com/api/chat.postMessage", params=payload)
			print(response.json())
		else:
			write_to_log(simulate_text)

def write_to_log(message_text, log=True):
	message_to_print = '{!s}   {!s}'.format(datetime.datetime.now(), message_text)
	message_to_log = '{!s}\n'.format(message_to_print)
	try:
		log_directory = os.environ['OPENSHIFT_LOG_DIR']
	except:
		print(message_text)
	else:
		log_file = '{!s}/log.txt'.format(log_directory)
		with open(log_file, 'a+') as file:
			file.write(message_to_log)

