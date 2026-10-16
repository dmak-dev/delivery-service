from app.service.main import (
    DeliveryBaseService,
    InternationalDelivery,
    DomesticDelivery,
    DeliveryService
)
from app.service.enums import Delivery
from app.service.entities import (
    DeliveryInput,
    DeliveryOutput,
    PostcodeInput,
    PostcodeOutput
)
from app.service.exceptions import (
    AddressNotRecognizedException,
    DeliveryException,
    DadataException
)
from app.service import messages
import pytest
import httpx


class TestDeliveryService:

    @pytest.mark.parametrize("name", Delivery.INTERNATIONAL)
    def test_calc__call_international_service__ok(
        self,
        name,
        mocker
    ):

        #arrange
        calc_input = DeliveryInput(
            type=name,
            weight=123.1,
            height=234.4,
            depth=345.5,
            width=456.6,
            is_safe=True
        )

        calc_result = DeliveryOutput(
            price=567.1,
            parcel_type="test"
        )

        calc_delivery_mock = mocker.patch(
            'app.service.main.InternationalDelivery.calculate',
            return_value=calc_result
        )

        service = DeliveryService()

        #act
        result = service.calc(data=calc_input)

        #assert
        calc_delivery_mock.assert_called_once_with(calc_input)
        assert result == calc_result

    @pytest.mark.parametrize("name", Delivery.DOMESTIC)
    def test_calc__call_domestic_service__ok(
        self,
        name,
        mocker
    ):

        #arrange
        calc_input = DeliveryInput(
            type=name,
            weight=123.1,
            height=234.4,
            depth=345.5,
            width=456.6,
            is_safe=True
        )

        calc_result = DeliveryOutput(
            price=567.1,
            parcel_type="test"
        )

        calc_delivery_mock = mocker.patch(
            'app.service.main.DomesticDelivery.calculate',
            return_value=calc_result
        )

        service = DeliveryService()

        #act
        result = service.calc(data=calc_input)

        #assert
        calc_delivery_mock.assert_called_once_with(calc_input)
        assert result == calc_result

    def test_calc__invalid_delivery__raise_exception(self):

        #arrange
        calc_input = DeliveryInput(
            type="WB",
            weight=123.1,
            height=234.4,
            depth=345.5,
            width=456.6,
            is_safe=True
        )

        #act
        with pytest.raises(DeliveryException) as ex:
            DeliveryService().calc(data=calc_input)

        #assert
        assert ex.value.message == messages.MSG_UNSUPPORTED_DELIVERY

    def test_postcode__success__ok(
        self,
        mocker
    ):

        # arrange
        postcode_input = PostcodeInput(
            address="test_address"
        )

        dadata_response = {
            "result": "test_full_address",
            "federal_district": "test_district",
            "city": "test_city",
            "street": "test_street",
            "postal_code": "123456",
            "timezone": "UTC+0"
        }

        postcode_output = PostcodeOutput(
            full_address="test_full_address",
            district="test_district",
            city="test_city",
            street="test_street",
            postcode="123456",
            timezone="UTC+0"
        )

        dadata_mock = mocker.patch("app.service.main.Dadata")
        dadata_instance = dadata_mock.return_value
        dadata_instance.clean.return_value = dadata_response

        service = DeliveryService()

        # act
        result = service.postcode(data=postcode_input)

        # assert
        dadata_instance.clean.assert_called_once_with(
            name="address",
            source="test_address"
        )
        assert result == postcode_output

    def test_postcode__connect_error__raise_exception(
        self,
        mocker
    ):

        # arrange
        postcode_input = PostcodeInput(
            address="test_address"
        )

        dadata_mock = mocker.patch("app.service.main.Dadata")
        dadata_instance = dadata_mock.return_value
        dadata_instance.clean.side_effect = httpx.ConnectError("error")

        service = DeliveryService()

        # act
        with pytest.raises(DadataException) as ex:
            service.postcode(data=postcode_input)

        # assert
        dadata_instance.clean.assert_called_once_with(
            name="address",
            source="test_address"
        )
        assert "error" in ex.value.details


class TestDeliveryCalculations:

    @pytest.mark.parametrize(
        "service_class, multiplier",
        [
            (DomesticDelivery, 1/2),
            (InternationalDelivery, 1.333),
        ]
    )
    @pytest.mark.parametrize("is_safe, expected_text", [
        (True, "Посылка застрахована. Хрупкий груз!"),
        (False, "В страховке отказано!")
    ])
    def test_calculate__ok(
        self,
        service_class,
        multiplier,
        is_safe,
        expected_text
    ):

        # arrange
        calc_input = DeliveryInput(
            type="test",
            weight=10,
            height=20,
            depth=30,
            width=40,
            is_safe=is_safe
        )

        service = service_class()

        # act
        result = service.calculate(data=calc_input)
        base = 40 + 30 + 20

        if service_class is DomesticDelivery:
            expected_price = 10 * base * multiplier
        else:
            expected_price = 10 * base * multiplier

        # assert
        assert result == DeliveryOutput(
            price=expected_price,
            parcel_type=expected_text
        )
    def test_postcode__address_not_recognized__raise_exception(
        self,
        mocker
    ):

        # arrange
        postcode_input = PostcodeInput(
            address="test_address"
        )

        dadata_mock = mocker.patch("app.service.main.Dadata")
        dadata_instance = dadata_mock.return_value
        dadata_instance.clean.return_value = {"result": None}

        service = DeliveryService()

        # act
        with pytest.raises(AddressNotRecognizedException) as ex:
            service.postcode(data=postcode_input)

        # assert
        assert ex.value.status_code == 400
        assert ex.value.message == messages.MSG_ADDRESS_NOT_RECOGNIZED
