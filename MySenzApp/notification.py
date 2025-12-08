from django.core.mail import send_mail
from django.conf import settings

class NotificationService:
    @staticmethod
    def send_email(subject, message, recipient_email):
        send_mail(subject,message,settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        
    @staticmethod
    def send_website_notification(user_id, title, message):
        # Example: push to WebSocket channel
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f"user_{user_id}",
        #     {
        #         "type": "notify",
        #         "title": title,
        #         "message": message,
        #     }
        # )
        print(f"[Website Notification] User {user_id}: {title} - {message}")

    @staticmethod
    def send_whatsapp(message, phone_number):
        # Example Twilio code (future):
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # client.messages.create(
        #     body=message,
        #     from_='whatsapp:+14155238886',  # Twilio sandbox number
        #     to=f'whatsapp:{phone_number}'
        # )
        print(f"[WhatsApp Notification] {phone_number}: {message}")

    @classmethod
    def notify_booking_update(cls, booking):
        subject = "Booking Update"
        customer_msg = (
            f"Hi {booking.user.name}, your booking {booking.booking_id} "
            f"for {booking.service.name} at {booking.store.store_name} "
            f"is now {booking.status}."
        )
        manager_msg = (
            f"Booking {booking.booking_id} updated.\n"
            f"Customer: {booking.user.name} ({booking.user.contact})\n"
            f"Service: {booking.service.name}\n"
            f"Store: {booking.store.store_name}\n"
            f"Status: {booking.status}"
        )

        # Notify customer
        cls.send_email(subject, customer_msg, booking.user.user.email)
        cls.send_website_notification(booking.user.user.id, subject, customer_msg)

        # Notify store manager (only one active manager per store)
        try:
            manager = booking.store.manager.get(is_active=True)
            cls.send_email(subject, manager_msg, manager.user.email)
            cls.send_website_notification(manager.user.id, subject, manager_msg)
        except Exception:
            pass