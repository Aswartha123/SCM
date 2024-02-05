from confluent_kafka import Consumer
import pymongo
import os
import json
from dotenv import load_dotenv
load_dotenv()

# MONGO_URL = os.getenv("mongodb")

# BS = os.getenv("bootstrap_server")
TOPIC = os.getenv("topic_name")

c = pymongo.MongoClient("mongodb+srv://Aswartha:aswartha@cluster0.brhrhhb.mongodb.net/")
db= c.get_database("Students")
col ="device_data" 
if col not in db.list_collection_names():
    db.create_collection(col)
col=db.device_data
consumer_config = {
    'bootstrap.servers':"kafka:9092",
    'group.id': 'learner',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit':False,
}
kafka_consumer = Consumer(consumer_config)

kafka_consumer.subscribe([TOPIC])

def upload_to_database(data:str):
    json_objects = data.split('}')
    for json_object in json_objects:
        # Check if the JSON object is not empty
        if json_object.strip():
            json_object += '}'
            try:
                document = json.loads(json_object)
                col.insert_one(document)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
try:
    count=1
    while count<=5:
        msg = kafka_consumer.poll(1.0)
        if msg is not None:
            data = msg.value().decode('utf-8')
            upload_to_database(data)
            print(data)
            count+=1
except KeyboardInterrupt:
    pass
finally:
    kafka_consumer.close()
    
        