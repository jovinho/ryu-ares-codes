import requests
import json

class EventApiService:
	def send_request(self):
		print("SENDING REQUEST")
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        r = requests.post('http://192.168.56.1:3002/event', data=json.dumps({'key':'value'}), headers=headers)
        print(r)
