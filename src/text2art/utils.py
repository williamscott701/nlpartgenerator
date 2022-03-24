import os
import pymongo
from datetime import datetime
from src.basic_func import get_value

db_link = get_value("config.yaml", 'MONGODB_SETTINGS.db_link')
client = pymongo.MongoClient(db_link)
db = client["Text2Art"]
user_collection = db["users"]
image_collection = db["users"]

def setup():
    dirs = ["models", "steps", os.path.join("data", "output"), os.path.join("data", "upload")]
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)

def get_queue(curr_time):
    return user_collection.count_documents({"time": {"$lte": curr_time}, "status": "queue"})

def queue(name, mail, prompts, aspect, quality, publish):
    curr_time = str(datetime.now())
    user_collection.insert_one({"name": name , "mail": mail, "prompts": prompts,
                                "aspect": aspect, "quality": quality, "publish": publish, 
                                "status": "queue", "time": curr_time})
    queue_no = get_queue(curr_time)
    return queue_no

def get_imgages(current, limit, by="top"):
    if by == "top":
        cursor = image_collection.find().sort([("like", pymongo.DESCENDING), ("downloads", pymongo.DESCENDING)]).limit(limit).skip(current*limit)
    elif by == "recent":
        cursor = image_collection.find().sort([("date", pymongo.DESCENDING)]).limit(limit).skip(current*limit)
    else:
        raise ValueError("Invalid by value. Must be 'top' or 'recent'.")

    imgs = {"filename": []}
    for img in cursor:
        imgs["filename"].append(img["filename"])
    return imgs