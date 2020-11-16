import os
from django.core.mail import send_mail




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

