import requests
import json

class EventApiService:
	def send_device_exit(self, datapath):
		print("DEVICE DISCONNECTED")
  		message = "O datapath " + str(datapath) + " se desconectou da rede"
		headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
  		body = {'status': 'DEVICE_DISCONNECTED', 'description': message, 'datapaths': [datapath]}
		r = requests.post('http://192.168.56.1:3002/event', data=json.dumps(body), headers=headers)
		print(r)

	def send_device_enter(self, datapath):
		print("DEVICE ENTERED")
		message = "Um novo datapath com o id " + str(datapath) + " se conectou a rede "
		headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
		body = {'status': 'DEVICE_CONNECTED', 'description': message, 'datapaths': [datapath]}
		r = requests.post('http://192.168.56.1:3002/event', data=json.dumps(body), headers=headers)
	
 	def send_flow_change(self, source, destination):
		print("FLOW_CHANGE")
		message = "Um caminho foi provisionado entre " + str(source) + " e " + str(destination)
		headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
		body = {'status': 'FLOW_CHANGE', 'description': message, 'datapaths': [source, destination]}
		r = requests.post('http://192.168.56.1:3002/event', data=json.dumps(body), headers=headers)
	# def send_request_another(self):
	# 	print("SENDING REQUEST")
	#     headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
	#     r = requests.post('http://192.168.56.1:3002/event', data=json.dumps({'key':'value'}), headers=headers)
	#     print(r)
		
	# def send_device_enter(self, datapath):
	#     print("DEVICE ENTERED")
	#     headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
	#     body = {'status': 'TOPOLOGY_UPDATE', 'description': 'Something has changed in the topology', 'datapaths': []}
	#     r = requests.post('http://192.168.56.1:3002/event', data=json.dumps(body), headers=headers)
		