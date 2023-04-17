from django.contrib.auth.models import User
from .models import CSVData
from knox.models import AuthToken
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework import status

class CsvDataTestCase(APITestCase):
    """
    Test suite for CsvData
    """
    DUMMY_CSV_DATA = 'review_time,team,date,merge_time\n30,Team A,2023-04-14,10\n25,Team B,2023-04-14,8\n20,Team A,2023-04-14,7\n15,Team B,2023-04-14,5'

    def setUp(self):
        """Set up the test suite"""
        self.first_user = User.objects.create_user(
            username="testuser1",
            password="test_password1"
        )
        self.second_user = User.objects.create_user(
            username="testuser2",
            password="test_password2"
        )

        _, self.token = AuthToken.objects.create(self.first_user)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    def test_create_csv_data_good_weather(self):
        # arrange

        # act
        response = self.client.post('/api/v1/csvdata/', data=CsvDataTestCase.DUMMY_CSV_DATA, content_type='text')

        # assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_csv_data_wrong_string(self):
        data = 'r'

        response = self.client.post('/api/v1/csvdata/', data, content_type='text')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_uploaded_data(self):
        # arrange
        self.client.post('/api/v1/csvdata/', data=CsvDataTestCase.DUMMY_CSV_DATA, content_type='text')
        
        # act
        response = self.client.get('/api/v1/csvdata/')
        
        # assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)

    def test_get_statistics(self):
        # arrange
        self.client.post('/api/v1/csvdata/', data=CsvDataTestCase.DUMMY_CSV_DATA, content_type='text')

        # act
        response = self.client.get('/api/v1/csvdata/statistics/')
        
        # assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
