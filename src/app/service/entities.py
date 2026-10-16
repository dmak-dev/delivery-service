from typing import TypedDict


class DeliveryInput(TypedDict):
    type: str
    width: float
    height: float
    depth: float
    weight: float
    is_safe: bool


class DeliveryOutput(TypedDict):
    price: float 
    parcel_type: str


class PostcodeInput(TypedDict):
    address: str


class PostcodeOutput(TypedDict):
    full_address: str
    district: str
    city: str
    street: str
    postcode: str
    timezone: str   
