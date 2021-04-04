import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import Command

class CommandSavingTests(TestCase):

    def test_can_create_command(self):
        command = Command.objects.create(
            name="run-code", description="Run code",
            input_schema="{}", output_schema="{}"
        )
        command.full_clean()
        self.assertEqual(str(command), "run-code")
        self.assertFalse(command.executions.all())