from firebase_admin import messaging

def send_push_notification(token, title, body):
    # Create a message to send to the device
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