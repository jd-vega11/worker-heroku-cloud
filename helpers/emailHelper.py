import os
import requests
from django.core.mail import send_mail

# text = ''
# designer_email_G = ''

# def sendEmail(designer_email, designer_name, design_datetime):
#     global text, designer_email_G
#     text = '''
#      Dear {},

#      We inform you that the design uploaded on {} 
#      was successfully processed and published 
#      in the public web-page of the company 
#      under the corresponding project.

#      Best regards,

#      Design Match 07 Team'''.format(designer_name, design_datetime)

#     designer_email_G = designer_email

#     send_simple_message()

# def send_simple_message():
#     return requests.post(
#         os.getenv('MAILGUN_SERVER_NAME'),
#         auth=("api", os.getenv('MAILGUN_ACCESS_KEY')),
#         data={"from": os.getenv('FROM_EMAIL'),
#             "to": [designer_email_G, 'maro96leon@hotmail.com'],
#             "subject": "Design processing finished",
#             "text": text})

def sendEmail(designer_email, designer_name, design_datetime):
    text = '''
     Dear {},
     We inform you that the design uploaded on {} 
     was successfully processed and published 
     in the public web-page of the company 
     under the corresponding project.
     Best regards,
     Design Match 07 Team'''.format(designer_name, design_datetime)

    send_mail(
        'Design processing finished',
        text,
        os.getenv('FROM_EMAIL'),
        [designer_email]
    )
