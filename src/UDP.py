from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient as UDPClient
from pythonosc.osc_server import BlockingOSCUDPServer as UDPServer

# import json
# import re


class UDP:
	def __init__(self, ip, client_port, server_port):
		self.dispatcher = Dispatcher()

		self.ip = ip
		self.client_port = client_port
		self.server_port = server_port

		self.client = UDPClient(self.ip, self.client_port)
		self.server = UDPServer((self.ip, self.server_port), self.dispatcher)

	def send(self, address_pattern, data):
		self.client.send_message(address_pattern, data)

	# def check_udp_communication(self, address_pattern):
	# 	self.dispatcher.map(address_pattern, self.check_message_format)
	# 	self.send(address_pattern, {"connected": False})
	# 	self.server.handle_request()
	# 	self.dispatcher.unmap(address_pattern, self.check_message_format)

	# def check_message_format(self, address_pattern, *args):
	# 	errors = []
	#
	# 	if address_pattern[1:] != "connect":
	# 		errors.append("OSC address pattern must be /connect")
	#
	# 	if len(args) == 0:
	# 		errors.append("OSC argument must not be empty")
	# 	if len(args) > 1:
	# 		errors.append("OSC argument must not have more than 1 element")
	#
	# 	message = args[0]
	# 	if not isinstance(message, str):
	# 		errors.append("OSC argument must be of type string")
	#
	# 	match = re.search("{([^}]+)}", str(message))
	# 	if match is None:
	# 		errors.append("OSC parsed argument must be of type JSON object")
	# 	else:
	# 		response = json.loads(message)
	#
	# 		if "errors" in response:
	# 			print_errors(response["errors"].split(", "))
	#
	# 		if not isinstance(response["connected"], bool):
	# 			errors.append("OSC parsed value must be of type boolean")
	#
	# 		if response["connected"]:
	# 			print(f"Successfully communicating with UDP client through port {self.client_port}")
	# 		else:
	# 			errors.append("Error while communicating with UDP client through port {}".format(self.client_port))
	#
	# 	if len(errors) > 0:
	# 		print_errors(errors)


# def print_errors(errors):
# 	for i in range(len(errors)):
# 		print(errors[i])
# 	exit(1)
