import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import Collection, Paper

class PaperCreationTests(TestCase):

    def test_can_create_paper(self):
        paper = mixer.blend(Paper)
        self.assertFalse(paper.collections.all())



class PaperOrderingTests(TestCase):

    def test_papers_ordered_by_year(self):
        paper1 = mixer.blend(Paper, year=2)
        paper2 = mixer.blend(Paper, year=1)
        paper3 = mixer.blend(Paper, year=4)
        self.assertEqual(list(Paper.objects.all()), [paper2, paper1, paper3])



class PaperCollectionsTests(TestCase):
    
    def test_paper_collections(self):
        paper = mixer.blend(Paper)
        collection1 = mixer.blend(Collection)
        paper.collections.add(collection1)
        self.assertEqual(list(paper.collections.all()), [collection1])