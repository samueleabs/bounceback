import firebase_admin
from firebase_admin import credentials, messaging
from .models import UserToken

# Initialize the Firebase app
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def send_push_notification(user, title, body):
    try:
        user_token = UserToken.objects.get(user=user)
        token = user_token.token

        # Create a message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )

        # Send the message
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except UserToken.DoesNotExist:
        print('User token not found')