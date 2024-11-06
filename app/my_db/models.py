from django.contrib.auth.models import AbstractUser
from django.db import models

from .compress import staff_image_folder, WEBPField
from .enums import UserStatus, StaffRole, NomType, NomUnit, QuantityStatus, OrderStatus, WorkStatus, PaymentStatus


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
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    role = models.IntegerField(choices=StaffRole.choices)
    salary = models.IntegerField(default=0)
    image = WEBPField(upload_to=staff_image_folder, blank=True, null=True)

    def __str__(self):
        return self.name


class ClientProfile(models.Model):
    user = models.OneToOneField(
        MyUser, on_delete=models.CASCADE, related_name='client_profile'
    )
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50, blank=True, null=True)
    company_title = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    image = WEBPField(upload_to=staff_image_folder, blank=True, null=True)

    def __str__(self):
        return self.name

# ______________________________ User end ______________________________


# ______________________________ General ______________________________

class Rank(models.Model):
    title = models.CharField(max_length=50)
    percent = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class SizeCategory(models.Model):
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Size(models.Model):
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(SizeCategory, on_delete=models.CASCADE, blank=True, null=True, related_name='sizes')

    def __str__(self):
        return self.title

# ______________________________ General end ______________________________


# ______________________________ Nomenclature ______________________________

class Nomenclature(models.Model):
    vendor_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50)
    type = models.IntegerField(choices=NomType.choices)
    unit = models.IntegerField(choices=NomUnit.choices)
    is_active = models.BooleanField(default=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    def __str__(self):
        return f'{self.title} - {self.vendor_code}'


class Pattern(models.Model):
    nomenclature = models.ForeignKey(Nomenclature, on_delete=models.CASCADE, related_name='patters')
    image = WEBPField(upload_to=staff_image_folder)

# ______________________________ Nomenclature end ______________________________


# ______________________________ Nomenclature Operation ______________________________

class Combination(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class Equipment(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class Operation(models.Model):
    title = models.CharField(max_length=50)
    time = models.IntegerField(default=0)  # secs
    price = models.DecimalField(max_digits=12, decimal_places=3)
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.CASCADE, related_name='operations'
    )
    combination = models.ForeignKey(
        Combination, on_delete=models.SET_NULL, blank=True, null=True, related_name='operations'
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.SET_NULL, blank=True, null=True, related_name='operations'
    )
    rank = models.ForeignKey(Rank, on_delete=models.SET_NULL, blank=True, null=True, related_name='operations')
    is_active = models.BooleanField(default=True)


class OperationSize(models.Model):
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='op_sizes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='op_sizes')


class Consumable(models.Model):
    operation_size = models.ForeignKey(OperationSize, on_delete=models.CASCADE, related_name='consumables')
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.SET_NULL, blank=True, null=True, related_name='consumables'
    )
    consumption = models.DecimalField(max_digits=12, decimal_places=3)
    waste = models.DecimalField(max_digits=12, decimal_places=3)

# ______________________________ Nomenclature Operation end ______________________________


# ______________________________ Warehouse ______________________________

class Warehouse(models.Model):
    title = models.CharField(max_length=50)
    staffs = models.ManyToManyField(StaffProfile, related_name='warehouses')
    address = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.title


class Quantity(models.Model):
    in_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name='in_quants'
    )
    out_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name='out_quants'
    )
    status = models.IntegerField(choices=QuantityStatus.choices, default=QuantityStatus.PROGRESSING)
    created_at = models.DateTimeField(auto_now_add=True)


class QuantityNomenclature(models.Model):
    quantity = models.ForeignKey(
        Quantity, on_delete=models.SET_NULL, blank=True, null=True, related_name='quantities'
    )
    nomenclature = models.ForeignKey(
        Nomenclature, on_delete=models.SET_NULL, blank=True, null=True, related_name='quantities'
    )
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)


class QuantityFile(models.Model):
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE, related_name='files')
    image = WEBPField(upload_to=staff_image_folder)


class QuantityHistory(models.Model):
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE, related_name='histories')
    staff_id = models.IntegerField()
    staff_name = models.CharField(max_length=50)
    staff_surname = models.CharField(max_length=50)
    status = models.IntegerField(choices=QuantityStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

# ______________________________ Warehouse end ______________________________


# ______________________________ Order ______________________________

class Order(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='orders')
    status = models.IntegerField(choices=OrderStatus.choices, default=OrderStatus.NEW)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    nomenclature = models.ForeignKey(Nomenclature, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)


class OrderProductAmount(models.Model):
    order_product = models.ForeignKey(OrderProduct, on_delete=models.CASCADE, related_name='amounts')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='amounts')
    amount = models.IntegerField(default=0)

# ______________________________ Order end ______________________________


# ______________________________ Work ______________________________

class Work(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='works')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='works')
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, blank=True, null=True, related_name='works')
    status = models.IntegerField(choices=WorkStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)


class WorkDetail(models.Model):
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='details')
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='details')
    amount = models.IntegerField()

# ______________________________ Work end ______________________________


# ______________________________ Payment ______________________________

class Payment(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='payments')
    status = models.IntegerField(choices=PaymentStatus.choices)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentFile(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='payments')

# ______________________________ Payment end ______________________________

