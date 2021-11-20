import time
from mixer.backend.django import mixer
from django.test import TestCase
from samples.models import Collection, Paper

class PaperCreationTests(TestCase):

    def test_can_create_paper(self):
        paper = mixer.blend(Paper)
        self.assertEqual(paper.url, None)



class PaperOrderingTests(TestCase):

    def test_papers_ordered_by_year(self):
        paper1 = mixer.blend(Paper, year=2)
        paper2 = mixer.blend(Paper, year=1)
        paper3 = mixer.blend(Paper, year=4)
        self.assertEqual(list(Paper.objects.all()), [paper2, paper1, paper3])