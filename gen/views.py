import os
import base64
from io import BytesIO
import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.http import JsonResponse
from django.shortcuts import render
from .models import User

# Create your views here.

def send_email_with_image(subject, body_text, body_html, from_email, to_email, image_path):
    msg = EmailMultiAlternatives(subject, body_text, from_email, [to_email])
    msg.attach_alternative(body_html, "text/html")

    # Attach the image
    with open(image_path, 'rb') as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-ID', '<image1>')
        msg.attach(mime_image)

    # Send the email
    try:
        msg.send()
        print('Email was sent successfully!')
    except Exception as e:
        print(f'An error occurred while sending email: {str(e)}')


def index(request):
    context = {}
    if request.method == 'POST':
        # Extract the data needed for generating the QR code
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        # Generate the content for the QR code
        qr_content = f"Name: {first_name} {last_name}\nEmail: {email}\nPhone: {phone}"

        if all([first_name, last_name, email, phone]):

            # Checking if the email address is already registered
            registered_user = User.objects.filter(email=email).first()
            if registered_user:
                return JsonResponse({"status": 100}) # Status 100 represent already registered email address
            
            # Create a QRCode instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)

            # Generate the QR code image
            qr_image = qr.make_image(fill='gold', back_color='white')

            # Save the QR code image to a specific path
            save_dir = os.path.join('gen/static/qrcode')
            os.makedirs(save_dir, exist_ok=True)  # Create directory if it doesn't exist
            save_path = os.path.join(save_dir, f'{first_name}{last_name}.png')
            qr_image.save(save_path)

            qr_image_pil = qr_image.get_image()
            stream = BytesIO()
            qr_image_pil.save(stream, format='PNG') 
            qr_image_data = stream.getvalue()
            qr_image_base64 = base64.b64encode(qr_image_data).decode()
            context['qr_image_base64'] = qr_image_base64   


            send_email_with_image(
                subject='QR Code Verification.',
                body_text=f'Dear {first_name},',
                body_html=f'''
                    <html>
                        <body>
                            <p>Your registration was successfully and your QR code is attached below.</p>
                            <img src="cid:image1" alt="QR Code" width="300"/>
                            <p>Regards,</p>
                            <p>JC50 Team </p>
                        </body>
                    </html>
                ''',
                from_email='',
                to_email=email,
                image_path = os.path.join(settings.BASE_DIR, 'gen', 'static', 'qrcode', f'{first_name}{last_name}.png'),
            )
            user = User(first_name=first_name, last_name=last_name, email=email, phone=phone, qr_code=qr_image_base64)
            user.save()
            return JsonResponse({"status": 200})  # Returns 200 if email was successfully sent

        else:
            return JsonResponse({"status": 400}) # Returns 400 if any of the form fields is not filled
    return render(request, 'index.html')

