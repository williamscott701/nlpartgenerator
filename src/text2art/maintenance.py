import sys
sys.path.append("pixray")
import os
import pixray

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl
import random
from PIL import Image, ImageDraw, ImageFont

from src.basic_func import get_value

#Opening Image & Creating New Text Layer
def watermark_image(input_file, output_file):
    img = Image.open(input_file).convert("RGBA")
    txt = Image.new('RGBA', img.size, (255,255,255,0))

    #Creating Text
    text = "sample text"
    font = ImageFont.load_default()

    #Creating Draw Object
    d = ImageDraw.Draw(txt)

    #Positioning Text
    width, height = img.size 
    textwidth, textheight = d.textsize(text, font)
    x=width-textwidth-1
    y=height-textheight-1

    #Applying Text
    d.text((x,y), text, fill=(255,255,255, 200), font=font)

    #Combining Original Image with Text and Saving
    watermarked = Image.alpha_composite(img, txt)
    watermarked.save(output_file)

def sendMail(name, mail_address, file_name):
    msg = MIMEMultipart()
    msg['From'] = get_value("config.yaml", "EMAIL.address")
    msg['To'] = mail_address
    msg['Subject'] = "Your Art is Ready!!"

    body = f"""
Hello {name},
Your art for prompts {file_name.split(".")[0]} is ready. Hope you will like it.
"""
    msg.attach(MIMEText(body, 'plain'))

    with open(os.path.join("data", "output",  file_name), "rb") as attachment:
        data = attachment.read()
    msg.attach(MIMEImage(data, name=file_name))

    try:
        context=ssl.create_default_context()
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
        server.ehlo()
        server.login(get_value("config.yaml", "EMAIL.address"), get_value("config.yaml", "EMAIL.password"))
        server.sendmail(get_value("config.yaml", "EMAIL.address"), mail_address, msg.as_string())
        server.close()

        return True
    except Exception as e:
        print("Somthing went wrong: ", e)
        return False

def generate(setting):
    seed = random.randint(0, 1000000)
    iteration = get_value("config.yaml", "MODEL.iteration")
    
    pixray.reset_settings()
    pixray.add_settings(prompts=setting["prompts"], aspect=setting["aspect"], quality=setting["quality"], 
                        iterations=iteration, seed=seed, vector_prompts="textoff", display_clear=True, 
                        output=os.path.join("data", "output", setting["prompts"]+".png"))

    settings = pixray.apply_settings()

    pixray.do_init(settings)
    pixray.do_run(settings)