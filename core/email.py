import re
from django.core.mail import send_mail

def send_welcome_email(user, hostname):
    """Sends an email welcoming a user to iMaps."""

    message = re.compile(r"  +").sub("", f"""Dear {user.name},
    <br><br>
    Thank you for signing up to the <a href=\"{hostname}\">iMaps platform</a>.
    Your username is {user.username} - to manage your account, visit
    <a href=\"{hostname}/settings/\">{hostname}/settings/</a>.
    <br><br>
    Best wishes,<br>
    Goodwright and the Ule Lab.""").strip()
    send_mail(
        subject="Welcome to iMaps",
        message=message,
        html_message=message,
        from_email="iMaps <noreply@imaps.goodwright.org>",
        recipient_list=[user.email],
        fail_silently=True
    )


def send_reset_email(user, reset_url):
    """Sends an email containing a code for resetting a password."""

    message = re.compile(r"  +").sub("", f"""Dear {user.name},
    <br><br>
    You recently requested a password reset for your account in the iMaps
    platform. To do so, click the following link and follow the instructions
    there:
    <br><br>
    <a href="{reset_url}">{reset_url}</a>
    <br><br>
    If you didn't request this, no action is required - only the recipeint of
    this email can reset your password.
    <br><br>
    The Ule Lab.""").strip()

    send_mail(
        subject="iMaps Password Reset",
        message=message,
        html_message=message,
        from_email="iMaps <noreply@imaps.goodwright.org>",
        recipient_list=[user.email],
        fail_silently=True
    )


def send_reset_warning_email(email):
    """Sends an email warning a user that their email was used in a password
    reset attempt."""

    message = re.compile(r"  +").sub("", f"""Dear {email},
    <br><br>
    You recently requested a password reset for this email, but it is not
    associated with any iMaps user account. Please check the email is correct.
    <br><br>
    The Ule Lab.""").strip()

    send_mail(
        subject="iMaps Password Reset",
        message=message,
        html_message=message,
        from_email="iMaps <noreply@imaps.goodwright.org>",
        recipient_list=[email],
        fail_silently=True
    )