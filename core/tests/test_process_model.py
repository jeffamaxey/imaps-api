import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import Process

class ProcessSavingTests(TestCase):

    def test_can_create_process(self):
        process = Process.objects.create(
            name="run-code", description="Run code",
            input_schema="{}", output_schema="{}"
        )
        process.full_clean()
        self.assertEqual(str(process), "run-code")
        self.assertFalse(process.executions.all())