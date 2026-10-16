from abc import ABC, abstractmethod
from dotenv import load_dotenv
from dadata import Dadata
from app.service.enums import Delivery
from app.service.entities import (
    DeliveryInput,
    DeliveryOutput,
    PostcodeInput,
    PostcodeOutput
)
from app.service import exceptions
import httpx
import os


load_dotenv()

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")


class DeliveryBaseService(ABC):

    @abstractmethod
    def calculate(self, data: DeliveryInput) -> DeliveryOutput:
        pass

    def check_parcel_safety(self, type: bool) -> str:
        return "Посылка застрахована. Хрупкий груз!" if type else "В страховке отказано!"


class DomesticDelivery(DeliveryBaseService):

    def calculate(self, data: DeliveryInput) -> DeliveryOutput:
        
        weight: float = data["weight"]
        width: float = data["width"]
        depth: float = data["depth"]
        height: float = data["height"]
        is_safe: bool = data["is_safe"]

        return DeliveryOutput(
            price=weight * (width + depth + height)/2,
            parcel_type=self.check_parcel_safety(is_safe)
        )
            

class InternationalDelivery(DeliveryBaseService):

    def calculate(self, data: DeliveryInput) -> DeliveryOutput:

        weight: float = data["weight"]
        width: float = data["width"]
        depth: float = data["depth"]
        height: float = data["height"]
        is_safe: bool = data["is_safe"]
        
        return DeliveryOutput(
            price=weight * (width + depth + height) * 1.333,
            parcel_type=self.check_parcel_safety(is_safe)
        )


class DeliveryService():

    def calc(self, data: DeliveryInput):

        type: str = data["type"]

        if type in Delivery.DOMESTIC:
            service = DomesticDelivery()
        elif type in Delivery.INTERNATIONAL:
            service = InternationalDelivery()
        else:
            raise exceptions.DeliveryException()
        return service.calculate(data)

    def postcode(self, data: PostcodeInput):

        address: str = data["address"]
        dadata = Dadata(API_KEY, SECRET_KEY)

        try:
            response = dadata.clean(name="address", source=address)
        except httpx.HTTPError as ex:
            # Сюда попадают и отказ соединения, и ошибки ответа сервиса, например 403 по ключам.
            raise exceptions.DadataException(details=str(ex))

        if not response.get("result"):
            raise exceptions.AddressNotRecognizedException()

        return PostcodeOutput(
            full_address=response["result"],
            district=response["federal_district"],
            city=response["city"],
            street=response["street"],
            postcode=response["postal_code"],
            timezone=response["timezone"]
        )
