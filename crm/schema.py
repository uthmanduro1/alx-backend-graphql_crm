import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Order, Product


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()
    
    def resolve_all_products(root, info):
        return Product.objects.all()
    
    def resolve_all_orders(root, info):
        return Order.objects.all()


schema = graphene.Schema(query=Query)