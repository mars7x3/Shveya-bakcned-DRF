# import requests
#
# url = "https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"
#
# payload = "token={TOKEN}&to=&body=WhatsApp API on UltraMsg.com works good"
# payload = payload.encode('utf8').decode('iso-8859-1')
# headers = {'content-type': 'application/x-www-form-urlencoded'}
#
# response = requests.request("POST", url, data=payload, headers=headers)
#
# print(response.text)