import re
from django.core.mail import send_mail

def send_welcome_email(user, hostname):

    message = re.compile(r"  +").sub("", f"""Dear {user.name},
    <br><br>
    Thank you for signing up to the <a href=\"{hostname}\">iMaps platform</a>.
    Your username is {user.username}.
    <br><br>
    The Ule Lab.""").strip()
    send_mail(
        subject="Welcome to iMaps",
        message=message,
        html_message=message,
        from_email="iMaps <noreply@imaps.goodwright.org>",
        recipient_list=[user.email],
        fail_silently=True
    )