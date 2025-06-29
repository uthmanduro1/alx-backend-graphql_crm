import graphene
from graphene_django import DjangoObjectType
from crm.models import Customer, Order, Product
from graphql import GraphQLError
import re
from django.db import transaction
from graphene_django.filter import DjangoFilterConnectionField
from .filters import CustomerFilter, ProductFilter, OrderFilter


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


def validate_phone(phone):
    pattern = r'^\+?\d[\d\-]{7,14}$'
    if phone and not re.match(pattern, phone):
        raise GraphQLError("Invalid phone format.")

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()


    def mutate(self, info, name, email, phone=None):
        validate_phone(phone)
        if Customer.objects.filter(email=email).exists():
            raise GraphQLError("Email already exists")
        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created sucessfully")
    

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customer = graphene.List(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        customers = []
        message = []

        with transaction.atomic():
            for entry in input:
                try:
                    validate_phone(entry.get("phone"))
                    if Customer.objects.filter(email=entry.get("email")).exists():
                        message.append(f"{entry['email']} already exists")
                        continue
                    customer = Customer.objects.create(**entry)
                    customers.append(customer)
                except Exception as e:
                    message.append(f"{entry.get('email', ['no email'])}: {str(e)}")
        return BulkCreateCustomers(customers=customers, message=message)
        

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):
        if price <= 0 or stock < 0:
            raise GraphQLError("price must be positive and stock must be non-negative")
        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)
    

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime()

    orger = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date):
        try:
            customer = Customer.objects.filter(id=customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Customer does not exists")
            
        if not product_ids:
            raise GraphQLError("At least one product must be selected")
        
        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            raise GraphQLError("One of the product is invalid")
        
        total_amount = sum(product.price for product in products)
        
        order = Order.objects.create(customer=customer, products=products, total_amount=total_amount)

        return CreateOrder(order=order)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter, order_by=graphene.List(of_type=graphene.String))
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter, order_by=graphene.List(of_type=graphene.String))
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter, order_by=graphene.List(of_type=graphene.String))
    
    def resolve_customers(self, info):
        return Customer.objects.all()
        
    def resolve_customer(self, info, id):
        return Customer.objects.get(id=id)
        
    def resolve_products(self, info):
        return Product.objects.all()
        
    def resolve_orders(self, info):
        return Order.objects.all()
    
    def resolve_all_customers(self, info, **kwargs):
        return Customer.objects.all().order_by(*kwargs.get("order_by", ["id"]))

    def resolve_all_products(self, info, **kwargs):
        return Product.objects.all().order_by(*kwargs.get("order_by", ["id"]))

    def resolve_all_orders(self, info, **kwargs):
        return Order.objects.all().order_by(*kwargs.get("order_by", ["id"]))

# Create the schema instance
crm_schema = graphene.Schema(query=Query, mutation=Mutation)

  