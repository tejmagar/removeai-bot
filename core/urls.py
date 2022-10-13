from django.urls import path

from core.views import BotReceiveMessage, ReceiveCallback

urlpatterns = [
    path('', BotReceiveMessage.as_view()),
    path('callback/', ReceiveCallback.as_view(), name='callback')
]
