import datetime
import json
from django.test import TestCase

from frontend.models import PCT


class TestAPIOrgViews(TestCase):

    fixtures = ['orgs', 'practices']
    api_prefix = '/api/1.0'

    def test_api_view_org_code(self):
        url = '%s/org_code?q=ainsdale&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'N84014')
        self.assertEqual(content[0]['name'], 'AINSDALE VILLAGE SURGERY')

        url = '%s/org_code?q=P87&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'P87629')
        self.assertEqual(content[0]['name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(content[0]['type'], 'practice')
        self.assertEqual(content[0]['setting'], 4)
        self.assertEqual(content[0]['setting_name'], 'GP Practice')

        url = '%s/org_code?q=03&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['code'], '03Q')
        self.assertEqual(content[0]['name'], 'NHS Vale of York')

    def test_api_view_org_code_org_type_open_ccgs_only(self):
        closed = PCT.objects.first()
        closed.close_date = datetime.date(2001, 1, 1)
        closed.save()

        url = '%s/org_code?q=03&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)

    def test_api_view_org_code_org_type(self):
        url = '%s/org_code?q=a&org_type=practice&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 3)
        self.assertEqual(content[0]['code'], 'P87629')
        self.assertEqual(content[0]['name'], '1/ST ANDREWS MEDICAL PRACTICE')

        url = '%s/org_code?q=a&org_type=CCG&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], '03Q')
        self.assertEqual(content[0]['name'], 'NHS Vale of York')

    def test_api_view_org_code_is_exact(self):
        url = '%s/org_code?q=N84014&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'N84014')
        self.assertEqual(content[0]['name'], 'AINSDALE VILLAGE SURGERY')

        url = '%s/org_code?q=P87&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 0)

    def test_api_view_all_orgs(self):
        url = '%s/org_code?format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 7)
        self.assertEqual(content[0]['code'], '03Q')
        self.assertEqual(content[0]['name'], 'NHS Vale of York')
        self.assertEqual(content[0]['type'], 'CCG')
        self.assertEqual(content[-1]['code'], 'B82018')
        self.assertEqual(content[-1]['name'], 'ESCRICK SURGERY')
        self.assertEqual(content[-1]['type'], 'practice')

    def test_stp_inexact_match(self):
        url = '%s/org_code?q=northampton&format=json&org_type=stp' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'E54000020')
        self.assertEqual(content[0]['name'], 'Northamptonshire')

    def test_stp_exact_match(self):
        url = '{}/org_code?q=E54000006&format=json&org_type=stp&exact=true'.format(
            self.api_prefix
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'E54000006')
        self.assertEqual(content[0]['name'], 'Humber, Coast and Vale')

    def test_regional_team_inexact_match(self):
        url = '{}/org_code?q=north&format=json&org_type=regional_team'.format(
            self.api_prefix
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'Y54')
        self.assertEqual(content[0]['name'], 'NORTH OF ENGLAND COMMISSIONING REGION')

    def test_regional_team_exact_match(self):
        url = '{}/org_code?q=Y55&format=json&org_type=regional_team&exact=true'.format(
            self.api_prefix
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'Y55')
        self.assertEqual(
            content[0]['name'],
            'MIDLANDS AND EAST OF ENGLAND COMMISSIONING REGION'
        )

    def test_pcn_inexact_match(self):
        url = '{}/org_code?q=transformational&format=json&org_type=pcn'.format(
            self.api_prefix
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'PCN0001')
        self.assertEqual(content[0]['name'], 'Transformational Sustainability')

    def test_pcn_exact_match(self):
        url = '{}/org_code?q=PCN0002&format=json&org_type=pcn&exact=true'.format(
            self.api_prefix
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'PCN0002')
        self.assertEqual(
            content[0]['name'],
            'Sustainable Transformation'
        )
