from django.contrib.auth.models import AbstractUser
from django.db import models

from .compress import staff_image_folder, WEBPField, equipment_image_folder, nom_image_folder
from .enums import UserStatus, StaffRole, NomType, NomUnit, QuantityStatus, OrderStatus, PaymentStatus, \
    PartyStatus


# ______________________________ User ______________________________

class MyUser(AbstractUser):
    status = models.IntegerField(choices=UserStatus.choices, null=True)


class StaffProfile(models.Model):
    user = models.OneToOneField(
        'MyUser', on_delete=models.CASCADE, related_name='staff_profile'
    )
    rank = models.ForeignKey(
        'Rank', on_delete=models.SET_NULL, blank=True, null=True, related_name='staff_profiles'
    )
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=50)
    role = models.IntegerField(choices=StaffRole.choices)
    salary = models.IntegerField(default=0)
    image = WEBPField(upload_to=staff_image_folder, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class ClientProfile(models.Model):
    user = models.OneToOneField(
        MyUser, on_delete=models.CASCADE, related_name='client_profile'
    )
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50, blank=True, null=True)
    company_title = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=50)
    address = models.CharField(max_length=50, blank=True, null=True)
    image = WEBPField(upload_to=staff_image_folder, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class ClientFile(models.Model):
    client = models.ForeignKey(
        ClientProfile, on_delete=models.CASCADE, related_name='files'
    )
    file = models.FileField(upload_to='client_files')

# ______________________________ User end ______________________________


# ______________________________ General ______________________________

class Rank(models.Model):
    title = models.CharField(max_length=50)
    percent = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']


class Size(models.Model):
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']


class Color(models.Model):
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']


# ______________________________ General end ______________________________


# ______________________________ Nomenclature ______________________________

class Nomenclature(models.Model):
    vendor_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50)
    type = models.IntegerField(choices=NomType.choices)
    unit = models.IntegerField(choices=NomUnit.choices, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    image = WEBPField(upload_to=nom_image_folder, blank=True, null=True)

    def __str__(self):
        return f'{self.title} - {self.vendor_code}'

    class Meta:
        ordering = ['-id']


class Pattern(models.Model):
    nomenclature = models.ForeignKey(Nomenclature, on_delete=models.CASCADE, related_name='patterns')
    image = WEBPField(upload_to=staff_image_folder)

# ______________________________ Nomenclature end ______________________________


# ______________________________ Nomenclature Operation ______________________________

class CombinationFile(models.Model):
    title = models.CharField(max_length=100)


class Combination(models.Model):
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.SET_NULL, blank=True, null=True, related_name='combinations'
    )
    operations = models.ManyToManyField('Operation', related_name='combinations')
    title = models.CharField(max_length=50)
    file = models.ForeignKey(CombinationFile, on_delete=models.SET_NULL, blank=True, null=True,
                             related_name='combinations')
    is_sample = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.id}. {self.title}'


class Equipment(models.Model):
    title = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    service_date = models.DateField(blank=True, null=True)
    guarantee = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title


class EquipmentImages(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='images'
    )
    image = WEBPField(upload_to=equipment_image_folder, blank=True, null=True)


class EquipmentService(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='services'
    )
    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name='services'
    )
    text = models.TextField()
    price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class Operation(models.Model):
    title = models.CharField(max_length=50)
    time = models.IntegerField(default=0)  # secs
    price = models.DecimalField(max_digits=12, decimal_places=3)
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.SET_NULL, related_name='operations', blank=True, null=True
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.SET_NULL, blank=True, null=True, related_name='operations'
    )
    rank = models.ForeignKey(Rank, on_delete=models.SET_NULL, blank=True, null=True, related_name='operations')
    is_active = models.BooleanField(default=True)
    is_sample = models.BooleanField(default=False)


class Consumable(models.Model):
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.CASCADE, related_name='consumables', blank=True, null=True
    )
    material_nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.CASCADE, related_name='material_consumables', blank=True, null=True
    )
    color = models.ForeignKey(
        Color, on_delete=models.SET_NULL, related_name='consumables', blank=True, null=True
    )
    consumption = models.DecimalField(max_digits=12, decimal_places=3)


class Price(models.Model):
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.CASCADE, related_name='prices',
    )
    title = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=3)

# ______________________________ Nomenclature Operation end ______________________________


# ______________________________ Warehouse ______________________________

class Warehouse(models.Model):
    title = models.CharField(max_length=50)
    staffs = models.ManyToManyField(StaffProfile, related_name='warehouses')
    address = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.id}. {self.title}'

    class Meta:
        ordering = ['-id']


class Quantity(models.Model):
    in_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name='in_quants'
    )
    out_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name='out_quants'
    )
    status = models.IntegerField(choices=QuantityStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)


class QuantityNomenclature(models.Model):
    quantity = models.ForeignKey(
        Quantity, on_delete=models.SET_NULL, blank=True, null=True, related_name='quantities'
    )
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.SET_NULL, blank=True, null=True, related_name='quantities'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    comment = models.TextField(blank=True, null=True)


class QuantityFile(models.Model):
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='quantity_files')


class QuantityHistory(models.Model):
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE, related_name='histories')
    staff_id = models.IntegerField()
    staff_name = models.CharField(max_length=50)
    staff_surname = models.CharField(max_length=50)
    status = models.IntegerField(choices=QuantityStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)


class NomCount(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, blank=True, null=True, related_name='counts'
    )
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.CASCADE, blank=True, null=True, related_name='counts'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)

# ______________________________ Warehouse end ______________________________


# ______________________________ Order ______________________________

class Order(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='orders')
    status = models.IntegerField(choices=OrderStatus.choices, default=OrderStatus.NEW)
    deadline = models.DateTimeField()
    true_deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    nomenclature = models.ForeignKey(Nomenclature, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    true_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    true_cost_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)


class OrderProductAmount(models.Model):
    order_product = models.ForeignKey(OrderProduct, on_delete=models.CASCADE, related_name='amounts')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, blank=True, null=True, related_name='amounts')
    amount = models.IntegerField(default=0)
    done = models.IntegerField(default=0)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL,blank=True, null=True, related_name='amounts')

# ______________________________ Order end ______________________________


# ______________________________ Work ______________________________

class Party(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='parties')
    nomenclature = models.ForeignKey(Nomenclature, on_delete=models.CASCADE, related_name='parties')
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='parties')
    number = models.CharField()
    status = models.IntegerField(choices=PartyStatus.choices, default=PartyStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)


class PartyDetail(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='details')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='party_details')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, blank=True, null=True, related_name='party_details')
    plan_amount = models.IntegerField(default=0)
    true_amount = models.IntegerField(default=0)


class PartyConsumable(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='consumptions')
    nomenclature = models.ForeignKey(Nomenclature, on_delete=models.CASCADE, related_name='party_cons')
    consumption = models.DecimalField(decimal_places=3, max_digits=12, default=0)
    defect = models.DecimalField(decimal_places=3, max_digits=12, default=0)
    left = models.DecimalField(decimal_places=3, max_digits=12, default=0)


class Work(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='works')
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True, related_name='works')
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, blank=True, null=True, related_name='works')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']


class WorkDetail(models.Model):
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='details')
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='works')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, blank=True, null=True, related_name='work_details')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL,blank=True, null=True, related_name='work_details')
    amount = models.IntegerField(default=0)


# ______________________________ Work end ______________________________


# ______________________________ Payment ______________________________

class Payment(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='payments')
    status = models.IntegerField(choices=PaymentStatus.choices)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField(default=0)

    class Meta:
        ordering = ['-id']


class PaymentFile(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='payments')

# ______________________________ Payment end ______________________________


# ______________________________ Plan ______________________________

class Plan(models.Model):
    income_amount = models.IntegerField(default=0)
    order_amount = models.IntegerField(default=0)
    date = models.DateField()

    class Meta:
        ordering = ['-id']

# ______________________________ Plan end ______________________________


# ______________________________ Calculation ______________________________

class Calculation(models.Model):
    vendor_code = models.CharField(max_length=50, blank=True, null=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class CalOperation(models.Model):
    calculation = models.ForeignKey(
        Calculation, on_delete=models.CASCADE, related_name='cal_operations'
    )
    operation = models.ForeignKey(
        Operation, on_delete=models.SET_NULL, related_name='cal_operations', blank=True, null=True
    )
    rank = models.ForeignKey(
        Rank, on_delete=models.SET_NULL, blank=True, null=True, related_name='cal_operations'
    )
    title = models.CharField(max_length=50)
    time = models.IntegerField(default=0)  # secs
    price = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)


class CalConsumable(models.Model):
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.CASCADE, related_name='cal_consumables', blank=True, null=True
    )
    calculation = models.ForeignKey(
        Calculation, on_delete=models.CASCADE, related_name='cal_consumables'
    )
    title = models.CharField(max_length=50)
    consumption = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.IntegerField(choices=NomUnit.choices, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)


class CalPrice(models.Model):
    calculation = models.ForeignKey(
        Calculation, on_delete=models.CASCADE, related_name='cal_prices'
    )
    title = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=3)


# ______________________________ Calculation end ______________________________

