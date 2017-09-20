import os
import channels.asgi

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cops_and_robbers.settings')
channel_layer = channels.asgi.get_channel_layer()
