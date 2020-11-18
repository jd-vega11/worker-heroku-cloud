from celery import shared_task
from projects.models import Designs
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
import uuid
import os
from pathlib import Path
from helpers import emailHelper
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import time
from random import randint
import re
import subprocess
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import boto3


@shared_task(bind=True)
def processDesigns(self, pending_design_id):

    pending_design = Designs.objects.get(design_uuid=pending_design_id)

    dyno_id = getUniqueIdentifierMachine()
    startFullTime = time.time()        
    try:
        pending_design.design_state = 'EN_PROCESO'
        pending_design.processing_start_date = timezone.now()
        pending_design.save(update_fields=['design_state', 'processing_start_date'])
    except Exception as update_error:
        self.update_state(state='FAILURE', meta={'exc': update_error})
        raise TaskFailure(str(update_error))
    
    startConversionTime = time.time()   
    try:
        #Get design
        design_original = pending_design.desing_original
        #Designer name
        name = pending_design.designer_name.split('\s')[0]
        last_name = pending_design.designer_lastname.split('\s')[0]
        designer_name =  '{} {}'.format(name, last_name)
        #Design datetime
        design_datetime = pending_design.created_at.strftime('%m/%d/%Y, %H:%M:%S')
        #Make the conversion
        desing_converted = createDesignConverted(design_original, designer_name, design_datetime)
        #Upload the fields in the database
    except Exception as conversion_err:
        self.update_state(state='FAILURE', meta={'exc': conversion_err})
        raise TaskFailure(str(conversion_err))
    
    endConversionTime = time.time() 

    if desing_converted is not None:
        startdatabaseUpdateTime = time.time()
        try:
            pending_design.desing_converted = desing_converted
            pending_design.design_state = 'DISPONIBLE'
            pending_design.processing_end_date = timezone.now()
            pending_design.save(update_fields=['desing_converted', 'design_state', 'processing_end_date'])
        except Exception as update_error:
            self.update_state(state='FAILURE', meta={'exc': update_error})
            raise TaskFailure(str(update_error))
        enddatabaseUpdateTime = time.time()
        
        startemailSendTime = time.time()

        try:
            emailHelper.sendEmail(pending_design.designer_email, designer_name, design_datetime)
        except Exception as send_email_error:
            print(send_email_error)
        
        endemailSendTime = time.time()
    else:
        try:                
            pending_design.design_state = 'ERROR_CONVERSION'
            pending_design.save(update_fields=['design_state'])
        except Exception as update_error:
            print(update_error)
    
    endFullTime = time.time()

    try:
        log_entry = '\n{},{},{},{},{},{}'.format(
            endFullTime-startFullTime,
            endConversionTime-startConversionTime,
            enddatabaseUpdateTime-startdatabaseUpdateTime,
            endemailSendTime-startemailSendTime,
            dyno_id,
            timezone.now()
            )

        saveTimeLogs(log_entry, dyno_id)            
    except Exception as log_error:
        print(log_error)

    

def createDesignConverted(design_original, designer_name, design_datetime):
    try:
        #Open image
        design_original.open()
        image = Image.open(design_original)

        #Verify format (if not PNG, convert)
        if image.format in ('JPEG', 'JPG'):
            image = image.convert('RGB')    

        #Resize image
        image = image.resize((800, 600))

        ##Add name and date
        font_path = os.path.join(settings.BASE_DIR, 'projects/static/fonts','robotomedium.ttf')
        font = ImageFont.truetype(font_path, 19)
        draw = ImageDraw.Draw(image)
        w, h = image.size
        footer = 'Designed for: {} \n Upload date: {}'.format(designer_name, design_datetime)
        text_w, text_h = draw.textsize(footer, font)

        draw.text(((w - text_w) // 2, h - text_h), footer, (255,255,255), font=font, align='center')

        ##Image filename and path definition
        filename = '{}.{}'.format(uuid.uuid4().hex, 'png')        
        image_bytes_io = BytesIO()  
        image.save(image_bytes_io, format='png')
        image.close()

        image_field_file = InMemoryUploadedFile(image_bytes_io, None, filename, "image/png", image_bytes_io.getbuffer().nbytes, None)
        
        return image_field_file

    except Exception as err:
        print(err)
        return None

def saveTimeLogs(log_entry, dyno_id):
    try:
        machineIdFileName = re.sub('[^0-9a-zA-Z]+', '_', dyno_id)
        log_filename = '{}.{}'.format(machineIdFileName, 'csv')            
        log_directory = "logs"
        log_path = os.path.join(log_directory, log_filename)

        client = boto3.client('s3')

        current_data_object = None
        try:                
            current_data = client.get_object(Bucket=os.getenv('AWS_STORAGE_BUCKET_NAME'), Key=log_path)
            current_data_object = current_data['Body'].read()
        except Exception as read_error:
            print(read_error)

        if current_data_object is not None:
            appended_data = current_data_object + log_entry.encode(encoding='UTF-8',errors='replace')
        else:
            appended_data = log_entry.encode(encoding='UTF-8',errors='replace')

        client.put_object(Body=appended_data, Bucket=os.getenv('AWS_STORAGE_BUCKET_NAME'), Key=log_path)           
            
    except Exception as log_error:
        print(log_error)

def getUniqueIdentifierMachine():
    try:
        dyno_id = os.getenv('DYNO')
        return str(dyno_id)
    except Exception as identifier_error:
        print(identifier_error)
        return "Worker1"
        

class TaskFailure(Exception):
   pass



