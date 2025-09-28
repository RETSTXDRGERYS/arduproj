import requests

# Replace with your Pico's IP (check console output from Pico script)
PICO_IP = "http://192.168.1.124"

# Blink LED
response = requests.get(f"{PICO_IP}/blink")
print(response.text)

# Just check root page
response = requests.get(PICO_IP)
print(response.text)
