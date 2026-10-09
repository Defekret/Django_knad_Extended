import json
import time

from django.test import TestCase

from .models import Phone


def create_phone(**kwargs):
    data = {
        'model_name': 'Pixel 6', 'brand': 'Google', 'price': 45000, 'color': 'black',
        'operation_system': 'Android', 'screen_size': 6.4, 'preview_text': 'text', 'rating': 8,
        'camera_resolution': 50, 'stock_quantity': 3, 'storage': 128,
    }
    data.update(kwargs)
    return Phone.objects.create(**data)


class ApiTest(TestCase):
    def setUp(self):
        self.pixel = create_phone()
        self.iphone = create_phone(model_name='iPhone 13', brand='Apple', price=80000, operation_system='iOS',
                                   screen_size=6.1, camera_resolution=12, stock_quantity=0, storage=256)

    def names(self, url):
        return [phone['model_name'] for phone in self.client.get(url).json()['items']]

    def test_list(self):
        response = self.client.get('/api/phones').json()
        self.assertEqual(response['total'], 2)
        self.assertEqual(len(response['items']), 2)

    def test_pagination(self):
        response = self.client.get('/api/phones?page=2&page_size=1').json()
        self.assertEqual(len(response['items']), 1)
        self.assertEqual(response['items'][0]['model_name'], 'iPhone 13')

    def test_detail(self):
        response = self.client.get(f'/api/phones/{self.pixel.id}')
        self.assertEqual(response.json()['model_name'], 'Pixel 6')
        self.assertEqual(self.client.get('/api/phones/100').status_code, 404)

    def test_create(self):
        data = {
            'model_name': 'Galaxy S20', 'brand': 'Samsung', 'price': 60000, 'color': 'blue',
            'operation_system': 'Android', 'screen_size': 6.2, 'preview_text': 'text', 'rating': 9,
            'camera_resolution': 64, 'stock_quantity': 5, 'storage': 128,
        }
        response = self.client.post('/api/phones', json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Phone.objects.count(), 3)

    def test_create_invalid(self):
        data = {'model_name': 'Galaxy S20', 'price': -5, 'rating': 100}
        response = self.client.post('/api/phones', json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('price', response.json()['errors'])
        self.assertIn('rating', response.json()['errors'])
        self.assertEqual(Phone.objects.count(), 2)

    def test_update(self):
        url = f'/api/phones/{self.pixel.id}'
        response = self.client.patch(url, json.dumps({'price': 40000}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.pixel.refresh_from_db()
        self.assertEqual(self.pixel.price, 40000)
        self.assertEqual(self.pixel.brand, 'Google')

        response = self.client.patch(url, json.dumps({'price': -1}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_delete(self):
        response = self.client.delete(f'/api/phones/{self.pixel.id}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Phone.objects.count(), 1)

    def test_filters(self):
        self.assertEqual(self.names('/api/phones?brand=apple'), ['iPhone 13'])
        self.assertEqual(self.names('/api/phones?os=android'), ['Pixel 6'])
        self.assertEqual(self.names('/api/phones?price_min=50000'), ['iPhone 13'])
        self.assertEqual(self.names('/api/phones?price_max=50000'), ['Pixel 6'])
        self.assertEqual(self.names('/api/phones?storage_min=200'), ['iPhone 13'])
        self.assertEqual(self.names('/api/phones?in_stock=true'), ['Pixel 6'])
        self.assertEqual(self.client.get('/api/phones?price_min=abc').status_code, 400)

    def test_search_and_ordering(self):
        self.assertEqual(self.names('/api/phones?search=pix'), ['Pixel 6'])
        self.assertEqual(self.names('/api/phones?ordering=-price'), ['iPhone 13', 'Pixel 6'])
        self.assertEqual(self.names('/api/phones?ordering=price'), ['Pixel 6', 'iPhone 13'])
        self.assertEqual(self.client.get('/api/phones?ordering=color').status_code, 400)

    def test_compare(self):
        response = self.client.get(f'/api/phones/compare?first={self.pixel.id}&second={self.iphone.id}').json()
        self.assertEqual(response['best_price'], 45000)
        self.assertEqual(response['best_screen_size'], 6.4)
        self.assertEqual(response['best_camera'], 50)
        self.assertEqual(response['best_storage'], 256)
        self.assertEqual(self.client.get('/api/phones/compare?first=1').status_code, 400)
        self.assertEqual(self.client.get('/api/phones/compare?first=1&second=100').status_code, 404)

    def test_favorites(self):
        self.client.post(f'/api/phones/{self.pixel.id}/favorite')
        self.assertEqual(self.names('/api/favorites'), ['Pixel 6'])
        self.client.delete(f'/api/phones/{self.pixel.id}/favorite')
        self.assertEqual(self.names('/api/favorites'), [])

    def test_stats(self):
        response = self.client.get('/api/stats').json()
        self.assertEqual(response['total'], 2)
        self.assertEqual(response['avg_price'], 62500)
        self.assertEqual(response['in_stock'], 1)
        self.assertEqual(len(response['brands']), 2)

    def test_health(self):
        self.assertEqual(self.client.get('/api/health').json(), {'status': 'ok'})

    def test_max_page_size(self):
        for i in range(150):
            create_phone(model_name=f'Phone {i}')
        response = self.client.get('/api/phones?page_size=1000').json()
        self.assertEqual(len(response['items']), 100)

    def test_speed(self):
        for i in range(1000):
            create_phone(model_name=f'Phone {i}')
        start = time.time()
        self.client.get('/api/phones?brand=Google&ordering=-price')
        self.assertLess(time.time() - start, 0.5)

    def test_old_pages(self):
        self.assertEqual(self.client.get('/phones/').status_code, 200)
        self.assertEqual(self.client.get(f'/phones/{self.pixel.id}').status_code, 200)
