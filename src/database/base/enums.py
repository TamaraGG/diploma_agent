import enum


class FileProcessingStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class CurrencyType(str, enum.Enum):
    RUB = "Рубли"
    FX = "Валюта"
    TOTAL = "Всего"

class DebtStatus(str, enum.Enum):
    TOTAL = "TOTAL"
    OVERDUE = "OVERDUE"

class RegionLevel(int, enum.Enum):
    COUNTRY = 0       # Российская Федерация
    DISTRICT = 1      # Федеральный округ
    REGION = 2        # Область/Край/Республика
    SUB_REGION = 3

class EntityType(str, enum.Enum):
    TOTAL = "Всего"
    LEGAL_ENTITY = "Юридические лица"
    INDIVIDUAL_ENTREPRENEUR = "Индивидуальные предприниматели"