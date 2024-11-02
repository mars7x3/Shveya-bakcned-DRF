from django.db import models

class UserStatus(models.IntegerChoices):
    STAFF = 1, 'СОТРУДНИК'
    CLIENT = 2, 'КЛИЕНТ'
    ADMIN = 777, 'АДМИН САЙТА'


class StaffRole(models.IntegerChoices):
    DIRECTOR = 1, 'ДИРЕКТОР'
    TECHNOLOGIST = 2, 'ТЕХНОЛОГ'
    WAREHOUSE = 3, 'ЗАВ СКЛАД'
    SEAMSTRESS = 4, 'ШВЕЯ'


"""
class NomTypeEnum(int, Enum):
    MATERIAL = 1  # сырье
    GP = 2  # готовый продукт
    PF_1 = 3  # полуфабрикат 1го уровня
    PF_2 = 4  # полуфабрикат 2го уровня


class NomUnitEnum(int, Enum):
    MM = 1  # мм
    SM = 2  # см
    M2 = 3  # м2
    L = 4  # литр
    
    
class OrderStatusEnum(int, Enum):
    NEW = 1  # новый
    DONE = 2  # готов
    PROGRESS = 3  # да
    OVERDUE = 4  # просрочен


class ImageActionEnum(int, Enum):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
"""