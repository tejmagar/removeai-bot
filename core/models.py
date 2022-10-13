from django.db import models

import uuid


# Create your models here.

class TaskGroup(models.Model):
    task_group = models.UUIDField(default=uuid.uuid4)
    chat_id = models.CharField(max_length=100)

    def __str__(self):
        return self.chat_id
