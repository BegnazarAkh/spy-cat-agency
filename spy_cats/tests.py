from decimal import Decimal
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from .models import SpyCat, Mission, Target
from .serializers import SpyCatSerializer, MissionCreateSerializer


class SpyCatModelTest(TestCase):
    def test_spycat_creation(self):
        cat = SpyCat.objects.create(
            name="Shadow",
            years_of_experience=5,
            breed="Siamese",
            salary=Decimal('50000.00')
        )
        self.assertEqual(cat.name, "Shadow")
        self.assertEqual(cat.years_of_experience, 5)
        self.assertEqual(cat.breed, "Siamese")
        self.assertEqual(cat.salary, Decimal('50000.00'))
        self.assertTrue(cat.created_at)
        self.assertTrue(cat.updated_at)

    def test_spycat_str_method(self):
        cat = SpyCat.objects.create(
            name="Shadow",
            years_of_experience=5,
            breed="Siamese",
            salary=Decimal('50000.00')
        )
        self.assertEqual(str(cat), "Shadow - Siamese")

    def test_spycat_fields(self):
        cat = SpyCat._meta.get_field('name')
        self.assertEqual(cat.max_length, 255)
        
        salary = SpyCat._meta.get_field('salary')
        self.assertEqual(salary.max_digits, 10)
        self.assertEqual(salary.decimal_places, 2)


class MissionModelTest(TestCase):
    def setUp(self):
        self.cat = SpyCat.objects.create(
            name="Shadow",
            years_of_experience=5,
            breed="Siamese",
            salary=Decimal('50000.00')
        )

    def test_mission_creation(self):
        mission = Mission.objects.create(cat=self.cat)
        self.assertEqual(mission.cat, self.cat)
        self.assertFalse(mission.complete)
        self.assertTrue(mission.created_at)

    def test_mission_str_method(self):
        mission = Mission.objects.create(cat=self.cat)
        self.assertEqual(str(mission), f"Mission {mission.id} - Incomplete")

    def test_mission_auto_complete(self):
        mission = Mission.objects.create(cat=self.cat)
        target = Target.objects.create(
            mission=mission,
            name="Target Alpha",
            country="Germany",
            complete=True
        )
        mission.save()
        mission.refresh_from_db()
        self.assertTrue(mission.complete)


class TargetModelTest(TestCase):
    def setUp(self):
        self.cat = SpyCat.objects.create(
            name="Shadow",
            years_of_experience=5,
            breed="Siamese",
            salary=Decimal('50000.00')
        )
        self.mission = Mission.objects.create(cat=self.cat)

    def test_target_creation(self):
        target = Target.objects.create(
            mission=self.mission,
            name="Target Alpha",
            country="Germany",
            notes="Initial notes"
        )
        self.assertEqual(target.mission, self.mission)
        self.assertEqual(target.name, "Target Alpha")
        self.assertEqual(target.country, "Germany")
        self.assertEqual(target.notes, "Initial notes")
        self.assertFalse(target.complete)

    def test_target_str_method(self):
        target = Target.objects.create(
            mission=self.mission,
            name="Target Alpha",
            country="Germany"
        )
        self.assertEqual(str(target), "Target Alpha (Germany)")


class SpyCatAPITest(APITestCase):
    def setUp(self):
        self.cat_data = {
            'name': 'Shadow',
            'years_of_experience': 5,
            'breed': 'Siamese',
            'salary': '50000.00'
        }

    @patch('requests.get')
    def test_create_spycat_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'name': 'Siamese'}]
        mock_get.return_value = mock_response

        url = reverse('spycat-list')
        response = self.client.post(url, self.cat_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SpyCat.objects.count(), 1)
        self.assertEqual(SpyCat.objects.get().name, 'Shadow')

    @patch('requests.get')
    def test_create_spycat_invalid_breed(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'name': 'Persian'}]
        mock_get.return_value = mock_response

        self.cat_data['breed'] = 'InvalidBreed'
        url = reverse('spycat-list')
        response = self.client.post(url, self.cat_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('breed', response.data)

    def test_list_spycats(self):
        SpyCat.objects.create(**self.cat_data)
        url = reverse('spycat-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_spycat(self):
        cat = SpyCat.objects.create(**self.cat_data)
        url = reverse('spycat-detail', kwargs={'pk': cat.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Shadow')

    def test_update_spycat_salary_only(self):
        cat = SpyCat.objects.create(**self.cat_data)
        url = reverse('spycat-detail', kwargs={'pk': cat.pk})
        update_data = {'salary': '60000.00', 'name': 'NewName'}
        response = self.client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.salary, Decimal('60000.00'))
        self.assertEqual(cat.name, 'Shadow')  # Name should not change

    def test_delete_spycat(self):
        cat = SpyCat.objects.create(**self.cat_data)
        url = reverse('spycat-detail', kwargs={'pk': cat.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SpyCat.objects.count(), 0)


class MissionAPITest(APITestCase):
    def setUp(self):
        self.cat = SpyCat.objects.create(
            name="Shadow",
            years_of_experience=5,
            breed="Siamese",
            salary=Decimal('50000.00')
        )
        self.mission_data = {
            'cat': self.cat.id,
            'targets': [
                {
                    'name': 'Target Alpha',
                    'country': 'Germany',
                    'notes': 'Initial notes'
                }
            ]
        }

    def test_create_mission_success(self):
        url = reverse('mission-list')
        response = self.client.post(url, self.mission_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Mission.objects.count(), 1)
        self.assertEqual(Target.objects.count(), 1)

    def test_create_mission_too_many_targets(self):
        self.mission_data['targets'] = [
            {'name': f'Target {i}', 'country': 'Country', 'notes': 'Notes'}
            for i in range(4)
        ]
        url = reverse('mission-list')
        response = self.client.post(url, self.mission_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('targets', response.data)

    def test_create_mission_no_targets(self):
        self.mission_data['targets'] = []
        url = reverse('mission-list')
        response = self.client.post(url, self.mission_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_missions(self):
        mission = Mission.objects.create(cat=self.cat)
        Target.objects.create(mission=mission, name='Target', country='Country')
        
        url = reverse('mission-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_mission(self):
        mission = Mission.objects.create(cat=self.cat)
        Target.objects.create(mission=mission, name='Target', country='Country')

        url = reverse('mission-detail', kwargs={'pk': mission.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['targets']), 1)

    def test_delete_mission_with_cat_fails(self):
        mission = Mission.objects.create(cat=self.cat)
        url = reverse('mission-detail', kwargs={'pk': mission.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_delete_mission_without_cat_success(self):
        mission = Mission.objects.create()
        url = reverse('mission-detail', kwargs={'pk': mission.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_assign_cat_to_mission(self):
        mission = Mission.objects.create()
        url = reverse('mission-assign-cat', kwargs={'pk': mission.pk})
        data = {'cat_id': self.cat.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mission.refresh_from_db()
        self.assertEqual(mission.cat, self.cat)

    def test_assign_cat_to_mission_already_assigned(self):
        mission = Mission.objects.create(cat=self.cat)
        url = reverse('mission-assign-cat', kwargs={'pk': mission.pk})
        data = {'cat_id': self.cat.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_target(self):
        mission = Mission.objects.create(cat=self.cat)
        target = Target.objects.create(mission=mission, name='Target', country='Country')
        
        url = reverse('mission-update-target', kwargs={'pk': mission.pk, 'target_id': target.pk})
        data = {'notes': 'Updated notes', 'complete': True}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target.refresh_from_db()
        self.assertEqual(target.notes, 'Updated notes')
        self.assertTrue(target.complete)

    def test_update_target_notes_on_completed_target_fails(self):
        mission = Mission.objects.create(cat=self.cat)
        target = Target.objects.create(
            mission=mission, 
            name='Target', 
            country='Country',
            complete=True
        )

        url = reverse('mission-update-target', kwargs={'pk': mission.pk, 'target_id': target.pk})
        data = {'notes': 'New notes'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SerializerTest(TestCase):
    def setUp(self):
        self.cat = SpyCat.objects.create(
            name="Shadow",
            years_of_experience=5,
            breed="Siamese",
            salary=Decimal('50000.00')
        )

    @patch('requests.get')
    def test_spycat_serializer_valid_breed(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'name': 'Siamese'}]
        mock_get.return_value = mock_response

        data = {
            'name': 'Test Cat',
            'years_of_experience': 3,
            'breed': 'Siamese',
            'salary': '40000.00'
        }
        serializer = SpyCatSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_mission_create_serializer_valid_targets(self):
        data = {
            'cat': self.cat.id,
            'targets': [
                {'name': 'Target 1', 'country': 'Country 1', 'notes': 'Notes 1'},
                {'name': 'Target 2', 'country': 'Country 2', 'notes': 'Notes 2'}
            ]
        }
        serializer = MissionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_mission_create_serializer_too_many_targets(self):
        data = {
            'cat': self.cat.id,
            'targets': [
                {'name': f'Target {i}', 'country': 'Country', 'notes': 'Notes'}
                for i in range(4)
            ]
        }
        serializer = MissionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('targets', serializer.errors)