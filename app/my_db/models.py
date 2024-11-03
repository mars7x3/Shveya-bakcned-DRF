from django.contrib.auth.models import AbstractUser
from django.db import models

from .compress import staff_image_folder, WEBPField
from .enums import UserStatus, StaffRole, NomType, NomUnit


# ______________________________ User ______________________________

class MyUser(AbstractUser):
    status = models.IntegerField(choices=UserStatus.choices, null=True)


class StaffProfile(models.Model):
    user = models.OneToOneField(
        'MyUser', on_delete=models.CASCADE, related_name='staff_profile'
    )
    rank = models.ForeignKey(
        'Rank', on_delete=models.SET_NULL, null=True, related_name='staff_profiles'
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

    def __str__(self):
        return self.title


class Size(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title

# ______________________________ General end ______________________________


# ______________________________ Nomenclature ______________________________

class Nomenclature(models.Model):
    vendor_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50)
    type = models.IntegerField(choices=NomType.choices)
    unit = models.IntegerField(choices=NomUnit.choices)

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


