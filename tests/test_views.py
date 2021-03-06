from datetime import date

from django.contrib.gis.geos import Polygon
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from imagery.models import Scene, SceneRequest

client = Client()
User = get_user_model()


class TestIndexView(TestCase):

    def test_index_response(self):
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)


class TestSceneDetailView(TestCase):

    def setUp(self):
        self.scene = Scene.objects.create(
            path='001',
            row='001',
            sat='L8',
            date=date(2015, 1, 1),
            name='LC80010012015001LGN00',
            cloud_rate=20.3,
            status='downloading'
            )

    def test_scene_detail_response(self):
        response = client.get(reverse('scene', args=[self.scene.name]))
        self.assertEqual(response.status_code, 200)


class TestGeoSceneDetailView(TestCase):

    def setUp(self):
        self.scene = Scene.objects.create(
            path='001',
            row='001',
            sat='L8',
            date=date(2015, 1, 1),
            name='LC80010012015001LGN00',
            cloud_rate=20.3,
            status='downloading'
            )

    def test_scene_detail_response(self):
        response = client.get(reverse('geoscene', args=[self.scene.name]))
        self.assertEqual(response.status_code, 200)


class TestGeoSceneListView(TestCase):

    def setUp(self):
        self.scene = Scene.objects.create(
            path='001',
            row='001',
            sat='L8',
            date=date(2015, 1, 1),
            name='LC80010012015001LGN00',
            cloud_rate=20.3,
            status='downloading',
            geom=Polygon(
                [
                    [-54.159229, -11.804765], [-56.405499, -11.291305],
                    [-55.990002, -9.499491], [-53.755329, -10.006503],
                    [-54.159229, -11.804765]
                ])
            )

        newScene = Scene.objects.create(
            path='001',
            row='001',
            sat='L8',
            date=date(2015, 2, 2),
            name='LC80010012015001LGNTD',
            cloud_rate=21.9,
            status='downloading',
            geom=Polygon(
                [
                    [-54.159229, -11.804765], [-56.405499, -11.291305],
                    [-55.990002, -9.499491], [-53.755329, -10.006503],
                    [-54.159229, -11.804765]
                ])
            )

    def test_geo_scene_detail_response(self):
        response = client.get(reverse('geoscene-listview'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 2)

    def test_geo_scene_pagination_response(self):

        for i in range(1,21):
            Scene.objects.create(
                path='001',
                row='001',
                sat='L8',
                date=date(2015, 2, 2),
                name='LC80010012015001LGN'.join("%02d" % i ),
                cloud_rate=21.9,
                status='downloading',
                geom=Polygon(
                    [
                        [-54.159229, -11.804765], [-56.405499, -11.291305],
                        [-55.990002, -9.499491], [-53.755329, -10.006503],
                        [-54.159229, -11.804765]
                    ])
                )

        self.assertEqual(Scene.objects.count(), 22)

        response = client.get(reverse('geoscene-listview'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 20)

        response = client.get(reverse('geoscene-listview'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 2)


class TestCloudRateView(TestCase):

    def test_cloud_rate_view(self):
        response = client.get(reverse('cloud-rate'))
        self.assertEqual(response.status_code, 200)


class TestSceneRequestView(TestCase):

    def setUp(self):
        Scene.objects.create(
            path='227',
            row='059',
            sat='L7',
            date=date(2015, 6, 3),
            name='LE72270592015154CUB00',
            cloud_rate=20.3,
            status='downloading'
        )
        self.user = User.objects.create_user('user', 'i@t.com', 'password')

    def test_unlogged_response(self):
        response = self.client.get(reverse('request-scene'))
        self.assertEqual(response.status_code, 302)

    def test_logged_response(self):
        response = self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LC80010012015001LGN00'}
        )
        self.assertEqual(response.status_code, 302)

        self.client.login(username=self.user.username, password='password')

        response = self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LC80010012015001LGN00'}
        )
        self.assertEqual(response.status_code, 200)

        # test uniqueness validation
        self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LC80010012015001LGN00'}
        )
        # test validation of scene_name field
        self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LE72270592015154CUB00'}
        )
        response = self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LE72270592015154CUB00_'}
        )
        response = self.client.post(
            reverse('request-scene'),
            {'scene_name': 'AE72270592015154CUB00'}
        )
        response = self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LE42270592015154CUB00'}
        )
        response = self.client.post(
            reverse('request-scene'),
            {'scene_name': 'LE72270592015154CUB0'}
        )

        self.assertEqual(SceneRequest.objects.count(), 1)


class TestSceneRequestViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('user', 'i@t.com', 'password')
        self.user2 = User.objects.create_user('another_user', 'i@t.com', 'password')
        self.scene_request = SceneRequest.objects.create(
                scene_name='LC82270592015001CUB00',
                user=self.user
        )
        self.scene_request2 = SceneRequest.objects.create(
                scene_name='LC82260592015001CUB00',
                user=self.user2,
                status='not_found'
        )

    def test_SceneRequestListView_response(self):
        response = self.client.get(reverse('user-scene-request'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username=self.user.username, password='password')

        response = self.client.get(reverse('user-scene-request'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['scenes'].count(), 1)

    def test_NotFoundSceneRequestListView_response(self):
        response = self.client.get(reverse('not-found-scene-request'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['scenes'].count(), 1)

    def test_SceneRequestDeleteView_unlogged_response(self):
        url = reverse('delete-scene-request', args=[self.scene_request.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(SceneRequest.objects.count(), 2)

    def test_SceneRequestDeleteView_logged_response(self):
        url = reverse('delete-scene-request', args=[self.scene_request.pk])

        self.client.login(username=self.user.username, password='password')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)

        url = reverse('delete-scene-request', args=[self.scene_request2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        self.assertEqual(SceneRequest.objects.count(), 1)
