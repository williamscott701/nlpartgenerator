import os
from datetime import datetime
import pymongo
from src.text2art.maintenance import generate, sendMail, watermark_image
from src.basic_func import get_value

db_link = get_value("config.yaml", 'MONGODB_SETTINGS.db_link')
client = pymongo.MongoClient(db_link)
db = client["Text2Art"]
user_collection = db["users"]
image_collection = db["images"]

if __name__ == '__main__':
    while True:
        try:
            user = user_collection.find({"status": "queue"}).sort([("time", pymongo.ASCENDING)]).limit(1)[0]
            print(f"user = {user}")
            print(f"Generating art for {user['_id']}")
        except IndexError:
            continue

        if user is not None:
            user_id = user["_id"]
            name = user["name"]
            setting = {"prompts": user["prompts"], "aspect": user["aspect"], "quality": user["quality"]}
            mail = user["mail"]
            publish = user["publish"]
            print(name, mail, setting)
            try:
                if user_collection.find_one({"prompts": setting["prompts"], "status": "done"}) is None:
                    status = generate(setting)

                    watermark_image(os.path.join("data", "output",  setting["prompts"]+".png"),
                                    os.path.join("data", "output",  setting["prompts"]+".png"))

                image_collection.insert_one({"name": name, "prompts": setting["prompts"],
                                             "filename": setting["prompts"]+".png", "publish": publish,
                                             "downloads": 0, "like": 0, "date": str(datetime.today())})
                                             
                status = sendMail(name, mail, setting["prompts"]+".png")
                if status:
                    status = {"status": "done"}
                else:
                    status = {"status": "mail_error"}
            except Exception as e:
                print(f"Error: {e}")
                status = {"status": "generation_error"}

            user_collection.update_one({"_id": user_id}, {"$set": status})
            print(f"{user['_id']} is done.\n")
        else:
            continue