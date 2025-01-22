# from firebase_admin import messaging

# def send_push_notification(token, title, body):
#     # Create a message to send to the device
#     message = messaging.Message(
#         notification=messaging.Notification(
#             title=title,
#             body=body,
#         ),
#         token=token,
#     )

#     # Send the message
#     response = messaging.send(message)
#     print('Successfully sent message:', response)

import json
from pywebpush import webpush, WebPushException
from django.conf import settings

def send_push_notification(subscription_info, body):
    try:
        # Debug statement to print the subscription_info dictionary
        print("Subscription Info:", subscription_info)

        if 'endpoint' not in subscription_info or 'keys' not in subscription_info:
            raise KeyError("Missing 'endpoint' or 'keys' in subscription_info")

        endpoint = subscription_info['endpoint']
        keys = subscription_info['keys']

        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {
                    "auth": keys['auth'],
                    "p256dh": keys['p256dh']
                }
            },
            data=json.dumps({"body": body}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}",
                "aud": "https://fcm.googleapis.com"
            }
        )
    except KeyError as e:
        print(f"KeyError: {e}")
    except WebPushException as ex:
        print("I'm sorry, Dave, but I can't do that: {}", repr(ex))
        # Mozilla returns additional information in the body of the response.
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}", extra.code, extra.errno, extra.message)