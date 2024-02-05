import socket
import os
from dotenv import load_dotenv
load_dotenv()

PORT = int(os.getenv("port"))
HOST = os.getenv("host")
BS = os.getenv("bootstrap_server")
TOPIC = os.getenv("topic_name")
print(PORT)     
ADDR = (HOST, PORT)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
while True:
    data = client.recv(1024).decode('utf-8')
    if not data:
        break
    from confluent_kafka import Producer
    producer_config={'bootstrap.servers':'kafka:9092'}
    producer = Producer(producer_config)
    send_data=producer.produce(TOPIC,data)
    producer.flush() 
    print("Received data from server:", data)
client.close()