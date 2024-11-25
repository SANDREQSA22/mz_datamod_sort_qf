from django.db import models
from django.db.models import Q, F
from django.utils.timezone import now
from datetime import timedelta

class Customer(models.Model):
    username = models.CharField(max_length=100, verbose_name="იუზერნეიმი")
    first_name = models.CharField(max_length=100, verbose_name="სახელი", default="")
    email = models.EmailField("ელ.ფოსტის მისამართი", unique=True)
    is_active = models.BooleanField("აქტიურია", default=False)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} ".strip() or self.email

    @staticmethod
    def username_contains_string_and_is_active(contained_string):
        return Customer.objects.filter(Q(username__contains=contained_string) & Q(is_active=True))
        

    @staticmethod
    def update_username_to_email():
        return Customer.objects.update(username=F("email"))

    @staticmethod
    def deactivate_customers_with_short_usernames(min_length):
        return Customer.objects.annotate(username_length=len('username')).filter(username_length__lt=min_length).update(is_active=False)

    
    @staticmethod
    def load_customers_without_email():
        return Customer.objects.defer('email')

    @staticmethod
    def customers_with_active_status_raw(active=True):
        from django.db import connection

        query = "SELECT * FROM app_customer WHERE is_active = %s"  
        with connection.cursor() as cursor:
            cursor.execute(query, [active])
            rows = cursor.fetchall()
            return rows


    @staticmethod
    def get_first_n_customers(n):
        return Customer.objects.all()[:n]


    @staticmethod
    def sort_customers_by_username():
        return Customer.objects.order_by('username')
        

    get_full_name.verbose_name = "სრული სახელი"

    class Meta:
        ordering = ("-id",)
        verbose_name = "მომხმარებელი"
        verbose_name_plural = "მომხმარებლები"

class Stadium(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    address = models.CharField(max_length=100, null=False, blank=False)
    capacity = models.IntegerField(null=False)

    def __str__(self):
        return self.name

    @staticmethod
    def stadiums_with_name_and_capacity(name, min_capacity):
        return Stadium.objects.filter(Q(name__icontains=name) & Q(capacity__gt=min_capacity))
    
    @staticmethod
    def double_capacity_for_large_stadiums(min_capacity):
        return Stadium.objects.filter(capacity__gt=min_capacity).update(capacity=F('capacity') * 2)


    @staticmethod
    def increase_capacity_by_sold_tickets(event_id):
        tickets_sold = Ticket.objects.filter(event_id=event_id).count()
        return Stadium.objects.filter(event=event_id).update(capacity=F('capacity') + tickets_sold)

    @staticmethod
    def load_stadiums_without_address():
        return Stadium.objects.defer('address')


    @staticmethod
    def stadiums_filtered_by_capacity_raw(min_capacity):
        from django.db import connection

        query = "SELECT * FROM app_stadium WHERE capacity > %s" 
        with connection.cursor() as cursor:
            cursor.execute(query, [min_capacity])
            rows = cursor.fetchall()
            return rows

    @staticmethod
    def get_top_n_stadiums_by_capacity(n):
        return Stadium.objects.order_by('-capacity')[:n]


    @staticmethod
    def sort_stadiums_by_name():
        return Stadium.objects.order_by('name')

class Event(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    date = models.DateTimeField(null=False, blank=False)
    stadium = models.ForeignKey(Stadium, null=False, blank=False, on_delete=models.DO_NOTHING)
    is_active = models.BooleanField("აქტიურია", null=False, default=True)

    def __str__(self):
        return self.name

    @staticmethod
    def extend_event_dates_by_days(days):
        return Event.objects.update(date=F('date') + timedelta(days=days))


    @staticmethod
    def deactivate_past_events():
        return Event.objects.filter(date__lt=now()).update(is_active=False)


    @staticmethod
    def adjust_event_name_with_stadium_name():
        return Event.objects.update(name=F('name') + " - " + F('stadium__name'))

    @staticmethod
    def load_events_without_stadium():
        return Event.objects.defer('stadium')

    @staticmethod
    def events_with_date_in_future_raw():
        from django.db import connection

        query = """
            SELECT * 
            FROM your_app_event  -- Replace 'your_app_event' with your actual table name
            WHERE date > NOW()
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def get_upcoming_events(limit):
        return Event.objects.filter(date__gte=now()).order_by('date')[:limit]


    @staticmethod
    def sort_events_by_name():
        return Event.objects.order_by('name')
    
class Ticket(models.Model):
    customer = models.ForeignKey(Customer, null=False, blank=False, on_delete=models.DO_NOTHING)
    event = models.ForeignKey(Event, null=False, blank=False, on_delete=models.CASCADE)
    bought_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.customer} -- {self.event}"

    @staticmethod
    def tickets_by_customer_or_event(customer_id, event_id):
        return Ticket.objects.filter(Q(customer_id=customer_id) | Q(event_id=event_id))

    @staticmethod
    def recent_tickets_excluding_event(event_id, days=30):
        time_threshold = now() - timedelta(days=days)
        return Ticket.objects.filter(Q(bought_at__gte=time_threshold) & ~Q(event_id=event_id))


    @staticmethod
    def apply_bulk_discount_to_recent_tickets(days=30, discount_percent=10):

        from django.db.models import F
        from django.utils.timezone import now
        from datetime import timedelta


        time_threshold = now() - timedelta(days=days)


        return Ticket.objects.filter(bought_at__gte=time_threshold).update(
            price=F('price') * (1 - discount_percent / 100)
        )

    @staticmethod
    def transfer_tickets_to_another_customer(old_customer_id, new_customer_id):
        return Ticket.objects.filter(customer_id=old_customer_id).update(customer_id=new_customer_id)

    @staticmethod
    def load_tickets_without_event():
        return Ticket.objects.defer('event')


    @staticmethod
    def tickets_for_event_raw(event_id):
        from django.db import connection

        query = "SELECT * FROM app_ticket WHERE event_id = %s" 
        with connection.cursor() as cursor:
            cursor.execute(query, [event_id])
            rows = cursor.fetchall()
            return rows


    @staticmethod
    def get_recent_tickets(limit):
        return Ticket.objects.order_by('-bought_at')[:limit]
    
    @staticmethod
    def sort_tickets_by_customer_name():
        return Ticket.objects.order_by('customer__first_name')
