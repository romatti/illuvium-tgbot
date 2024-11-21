import requests
import json

TOKEN = '7642633597:AAH_6GDWxeNVSUYtg0IcqdET-n3-Q-Xsd-A'

URL = 'https://api.telegram.org/bot{TOKEN}/{method}'

updates = 'getUpdates'
send = 'sendMessage'

data = {
    'chat_id': '56140962',
    'text': 'hello from bot',
    }

url = URL.format(TOKEN=TOKEN, method=send)


# response = requests.get(url)
response = requests.post(url, data=data)
json_content = json.loads(response.text)


print(response)
