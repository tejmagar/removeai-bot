import os
import shutil
from pathlib import Path

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import json
import requests

from core.models import TaskGroup

BOT_TOKEN = os.environ['BOT_TOKEN']


# Create your views here.

def get_file_path(file_id):
    api_url = f'https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}'
    response = requests.get(api_url).text
    data = json.loads(response)
    result = data.get('result')
    file_path = result.get('file_path')
    return file_path


def download_file(file_path):
    api_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}'

    filename = str(Path(file_path).name)
    tmp_dir = Path('tmp')
    if not tmp_dir.exists():
        tmp_dir.mkdir()

    out_path = f'tmp/{filename}'

    with requests.get(api_url, stream=True) as r:
        with open(out_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return out_path


def upload_file(task_group, file_path, callback_url):
    files = {
        'original_image': open(file_path, 'rb')
    }

    data = {
        'task_group': task_group,
        'callback_url': callback_url
    }

    api_url = 'https://erasebg.org/api/1/background-remover/upload/'
    r = requests.post(api_url, files=files, data=data)
    print(r.text)


def get_current_host(request) -> str:
    scheme = request.is_secure() and "https" or "http"
    return f'{scheme}://{request.get_host()}'


@method_decorator(csrf_exempt, name='dispatch')
class BotReceiveMessage(View):
    def post(self, request):
        request_body = request.body.decode('UTF-8')
        data = json.loads(request_body)

        message = data.get('message')
        chat = message.get('chat')
        firstname = chat.get('first_name')
        chat_id = chat.get('id')
        photos = message.get('photo', None)

        send_message(chat_id,
                     f'Hi {firstname}, your task is received. We are currently processing it. It might take few seconds.')

        if photos and len(photos) > 0:
            photo = photos[-1]
            file_id = photo.get('file_id')
            path = get_file_path(file_id)
            out_path = download_file(path)

            model = TaskGroup.objects.create(chat_id=chat_id)

            upload_file(str(model.task_group), out_path, f'{get_current_host(request)}/callback/')
        return HttpResponse({})


def send_message(chat_id, text=None, photo_url=None, type_photo=False):
    type_t = 'sendMessage'

    if type_photo:
        type_t = 'sendPhoto'

    api_url = f'https://api.telegram.org/bot{BOT_TOKEN}/{type_t}'

    data = {
        'chat_id': chat_id,
    }

    if text:
        data['text'] = text

    if photo_url:
        data['photo'] = photo_url

    r = requests.post(api_url, json=data)
    print(r.text)


@method_decorator(csrf_exempt, name='dispatch')
class ReceiveCallback(View):
    def post(self, request):
        print(request.body)
        request_body = request.body.decode('UTF-8')
        data = json.loads(request_body)

        processed_image = f'https://erasebg.org{data.get("processed_image")}'
        print(processed_image)

        task_group = data.get('task_group')
        chat_id = TaskGroup.objects.get(task_group=task_group).chat_id
        send_message(chat_id, 'Your image background has been removed.')
        send_message(chat_id, 'yes', processed_image, type_photo=True)

        return HttpResponse('OK')
