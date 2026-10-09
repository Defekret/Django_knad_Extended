from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Phone(models.Model):
    image = models.ImageField(upload_to='phones/', default='phones/default.png')
    model_name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
    price = models.FloatField(validators=[MinValueValidator(0)])
    color = models.CharField(max_length=200)
    operation_system = models.CharField(max_length=200)
    screen_size = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    preview_text = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    camera_resolution = models.FloatField(validators=[MinValueValidator(0)])
    stock_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    storage = models.IntegerField(default=128, validators=[MinValueValidator(1)])
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.brand} {self.model_name}'

    def get_absolute_url(self):
        return reverse('phone-detail', args=[str(self.id)])
