from django import forms
from .models import Product, Budget


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ('name', 'value')
        labels = {
            'name': 'Name',
            'value': 'Value'
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'price', 'quantity', 'buyDate', 'budget')
        labels = {
            'name': 'Name',
            'price': 'Price',
            'quantity': 'Quantity',
            'buyDate': 'Buy date',
            'budget': 'Budget'
        }