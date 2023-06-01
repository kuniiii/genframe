import time
import random
import requests
from secrets import SLACK_BOT_TOKEN

# List of words to randomly choose from
words = ["apple", "banana", "cherry", "date", "elderberry"]

def send_random_message(channel_id):
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": "Bearer " + SLACK_BOT_TOKEN}
    payload = {
        "channel": channel_id,
        "text": random.choice(words)  # Select a random word from the list
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Error sending message: {response.content}")

channel_id = "C057W6XF01J"

while True:
    send_random_message(channel_id)
    time.sleep(10)  # Wait for 10 seconds before sending the next message
