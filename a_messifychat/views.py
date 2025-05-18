from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *

# Create your views here.
@login_required
def chat_view(request):
    group = get_object_or_404(ChatGroup, group_name='public-chat')
    chat_messages = group.chat_messages.all()
    form = ChatmessageCreateForm()

    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = group
            message.save()
            context = {
                'message' : message,
                'user' : request.user,
            }
            return render(request, 'a_messifychat/partials/chat_message_p.html', context)

    return render(request, 'a_messifychat/chat.html', {'chat_messages' : chat_messages, 'form' : form})