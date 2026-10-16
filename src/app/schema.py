from marshmallow import Schema, validate
from marshmallow.fields import (
    Float,
    String,
    Boolean
)
from marshmallow.decorators import post_load
from app.service.entities import (
    DeliveryInput,
    PostcodeInput
)
from app.service.enums import Delivery


class DeliverySchema(Schema):

    type = String(
        load_only=True,
        required=True,
        validate=validate.OneOf(
            Delivery.VALUES,
            error=f"Допустимые перевозчики: {', '.join(Delivery.VALUES)}.",
        ),
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается строка"},
    )
    width = Float(
        load_only=True,
        required=True,
        # Нулевые и отрицательные габариты дают бессмысленную цену.
        validate=validate.Range(
            min=0, min_inclusive=False, error="Значение должно быть больше нуля",
        ),
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается число"},
    )
    height = Float(
        load_only=True,
        required=True,
        validate=validate.Range(
            min=0, min_inclusive=False, error="Значение должно быть больше нуля",
        ),
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается число"},
    )
    depth = Float(
        load_only=True,
        required=True,
        validate=validate.Range(
            min=0, min_inclusive=False, error="Значение должно быть больше нуля",
        ),
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается число"},
    )
    weight = Float(
        load_only=True,
        required=True,
        validate=validate.Range(
            min=0, min_inclusive=False, error="Значение должно быть больше нуля",
        ),
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается число"},
    )
    is_safe = Boolean(
        load_only=True,
        required=True,
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается логическое значение"},
    )

    price = Float(dump_only=True)
    parcel_type = String(dump_only=True)

    @post_load
    def make_delivery_input(self, data, **kwargs) -> DeliveryInput:
        return DeliveryInput(**data)


class PostcodeSchema(Schema):

    address = String(
        load_only=True,
        required=True,
        error_messages={"required": "Поле обязательно", "invalid": "Ожидается строка"},
    )

    full_address = String(dump_only=True)
    district = String(dump_only=True)
    city = String(dump_only=True)
    street = String(dump_only=True)
    postcode = String(dump_only=True)
    timezone = String(dump_only=True)

    @post_load
    def make_postcode_data(self, data, **kwargs):
        return PostcodeInput(**data)

