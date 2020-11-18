import os
from sendgrid.helpers.mail import Mail
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

    message = Mail(
        from_email = os.getenv('FROM_EMAIL'),
        to_emails = designer_email,
        subject='Design processing finished',
        plain_text_content=text
        send_mail('Design processing finished', 
        text, 
        os.getenv('FROM_EMAIL')),
        [designer_email]
    )

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

