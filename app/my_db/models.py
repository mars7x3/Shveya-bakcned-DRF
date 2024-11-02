from django.contrib.auth.models import AbstractUser
from django.db import models

from .compress import staff_image_folder, WEBPField
from .enums import UserStatus, StaffRole


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

