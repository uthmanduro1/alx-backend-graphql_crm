from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

# Create your models here.
class Customer(models.Model):
    name=models.CharField(blank=False, null=False, max_length=100)
    email=models.CharField(blank=False, null=False, unique=True, max_length=100)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$',
                message='Phone must be in format +1234567890 or 123-456-7890'
            )
        ]
    )

    def __str__(self):
        return self.name
    

class Product(models.Model):
    name=models.CharField(blank=False, null=False, max_length=100)
    price=models.DecimalField(blank=False, null=False, max_digits=24, decimal_places=2, validators=[
        MinValueValidator(0.01)])
    stock=models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_id} {self.product_ids}"
