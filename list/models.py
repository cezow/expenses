from django.db import models
import datetime, random


class Budget(models.Model):
    name = models.CharField(max_length=64)
    value = models.DecimalField(decimal_places=2, max_digits=8, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"
    
    def color(self):
        return f'rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.5)' 


class Product(models.Model):
    name = models.CharField(max_length=64)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    quantity = models.IntegerField(default=1)
    buyDate = models.DateField(default=datetime.date.today, null=False)
    budget = models.ForeignKey(Budget, null=True, on_delete=models.SET_NULL, blank=True, related_name="products")

    def __str__(self):
        return self.name

    def total(self):
        return self.price * self.quantity