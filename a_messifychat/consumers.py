from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from .models import *
from .chatbot import Chatbot
import json
import threading

class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)
        
        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )

        self.chatbot = Chatbot()

        if self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )

        if self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()

    def update_online_count(self):
        online_count = self.chatroom.users_online.count()
        event = {
            'type': 'online_count_handler',
            'online_count': online_count,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def online_count_handler(self, event):
        online_count = event['online_count']
        html = render_to_string(
            'a_messifychat/partials/online_count.html',
            {'online_count': online_count}
        )
        self.send(text_data=html)

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        body = text_data_json['body']

        message = GroupMessage.objects.create(
            body=body,
            author=self.user,
            group=self.chatroom
        )

        event = {
            'type' : 'message_handler',
            'message_id' : message.id,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

        if '@bot' in body:
            threading.Thread(target=self.handle_bot_response, args=(body,)).start()

    def handle_bot_response(self, message):
        user_message = message.replace('@bot', '')
        previous_messages = self.chatroom.chat_messages.all()
        chat_log = "\n".join([f"{msg.author.username}: {msg.body}" for msg in previous_messages])

        bot_response = self.chatbot.get_response(user_message, chat_log).content

        User = get_user_model()
        bot_user = User.objects.get(username='bot')
        bot_message = GroupMessage.objects.create(
            body=bot_response,
            author=bot_user,
            group=self.chatroom
        )

        event = {
            'type' : 'message_handler',
            'message_id' : bot_message.id,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def message_handler(self, event):
        message_id = event['message_id']
        message = GroupMessage.objects.get(id=message_id)
        context = {
            'message': message,
            'user': self.user,
        }
        html = render_to_string(
            "a_messifychat/partials/chat_message_p.html",
            context=context
        )
        self.send(text_data=html)