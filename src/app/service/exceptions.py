from typing import Optional, Any
from app.service import messages


class ServiceException(Exception):

    default_message = None
    status_code = 500

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class ClientException(ServiceException):
    """Ошибка вызвана данными запроса, поэтому ответ 400, а не 500."""

    status_code = 400


class DeliveryException(ServiceException):
    default_message = messages.MSG_UNSUPPORTED_DELIVERY


class DadataException(ServiceException):
    default_message = messages.MSG_DADATA_UNAVAILABLE


class AddressNotRecognizedException(ClientException):
    default_message = messages.MSG_ADDRESS_NOT_RECOGNIZED
