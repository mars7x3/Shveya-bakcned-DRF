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
    CUTTER = 5, 'КРОЙЩИК'
    CONTROLLER = 6, 'КОНТРОЛЛЕР'
    OTK = 7, 'ОТК'


class NomType(models.IntegerChoices):
    MATERIAL = 1, 'СЫРЬЕ'
    PF_1 = 2, "ПФ1"
    PF_2 = 3, "ПФ2"
    GP = 4, "ГП"
    ORDER = 5, "ЗАКАЗ"



class NomStatus(models.IntegerChoices):
    CUT = 1, 'КРОЙ'
    SHOP = 2, "ЦЕХ"


class NomUnit(models.IntegerChoices):
    MM = 1, "ММ"
    SM = 2, "СМ"
    M2 = 3, "М2"
    L = 4, "ЛИТР"
    U = 5, "ШТ."
    R = 6, "РУЛОН"
    BB = 7, "БОБИНЫ"
    BX = 8, "КОРОБКИ"
    M = 9, "МЕТР"


class OrderStatus(models.IntegerChoices):
    NEW = 1, "НОВЫЙ"
    DONE = 2, "ГОТОВ"
    PROGRESS = 3, "В ПРОЦЕССЕ"
    OVERDUE = 4, "ПРОСРОЧЕН"


class QuantityStatus(models.IntegerChoices):
    PROGRESSING = 1, "В ОБРАБОТКЕ"
    ACTIVE = 2, "УСПЕШНОЕ ПЕРЕМЕЩЕНИЕ"
    INACTIVE = 3, "ОТМЕНА ПЕРЕМЕЩЕНИЯ"
    WRITE_OF = 4, "СПИСАНИЕ"
    RETURN_TO_CLIENT = 5, "ВОЗВРАТ КЛИЕНТУ"
    DEFECT = 6, "БРАК"
    ORDER = 7, "ЗАКАЗ"


class PartyStatus(models.IntegerChoices):
    NEW = 1, "НОВЫЙ"
    MODERATED = 2, "ПРОВЕРЕН"


class PaymentStatus(models.IntegerChoices):
    SALARY = 1, "ЗП"
    FINE = 2, "ШТРАФ"
    ADVANCE = 3, "АВАНС"
    FINE_CHECKED = 4, "ШТРАФ - учтен"
    ADVANCE_CHECKED = 5, "АВАНС - учтен"
    BONUS = 6, "БОНУС"


class WorkStatus(models.IntegerChoices):
    NEW = 1, "НОВЫЙ"
    PAID = 2, "ОПЛАЧЕН"


class CombinationStatus(models.IntegerChoices):
    ZERO = 0, "НЕТ"
    OTK = 1, "ОТК"
    DONE = 2, "УПАКОВКА"
    CUT = 3, 'КРОЙ'

