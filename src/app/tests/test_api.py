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
from app.service.enums import Delivery
from marshmallow import ValidationError
from app.service import messages

def test_calc__ok(client, mocker):

    #arrange
    calc_result = DeliveryOutput(
        price=123.4,
        parcel_type="test"
    )

    check_mock = mocker.patch(
        "app.service.main.DeliveryService.calc",
        return_value=calc_result
    )

    #act
    response = client.post(
        path='/calc',
        json={
            "type": "CDEK",
            "width": 123.4,
            "height": 234.5,
            "depth": 345.6,
            "weight": 12,
            "is_safe": True
        }
    )

    #assert
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['price'] == calc_result['price']
    assert response.json['parcel_type'] == calc_result['parcel_type']
    check_mock.assert_called_once_with(
        data=DeliveryInput(
            type="CDEK",
            width=123.4,
            height=234.5,
            depth=345.6,
            weight=12,
            is_safe=True
        )
    )

def test_calc__validation_error__bad_request(client, mocker):

    # arrange
    calc_mock = mocker.patch(
        "app.service.main.DeliveryService.calc"
    )

    # act
    response = client.post(
        path="/calc",
        json={
            "type": "CDEK",
            "width": 123.4
        }
    )

    # assert
    assert response.status_code == 400
    assert response.content_type == "application/json"
    calc_mock.assert_not_called()


def test_calc__service_exception__internal_server_error(client, mocker):

    # arrange
    calc_mock = mocker.patch(
        "app.service.main.DeliveryService.calc",
        side_effect=DeliveryException(details="test error")
    )

    # act
    response = client.post(
        path="/calc",
        json={
            "type": "CDEK",
            "width": 123.4,
            "height": 234.5,
            "depth": 345.6,
            "weight": 12,
            "is_safe": True
        }
    )

    # assert
    assert response.status_code == 500
    assert response.content_type == "application/json"
    calc_mock.assert_called_once_with(
        data=DeliveryInput(
            type="CDEK",
            width=123.4,
            height=234.5,
            depth=345.6,
            weight=12,
            is_safe=True
        )
    )


def test_postcode__ok(client, mocker):

    # arrange
    postcode_result = PostcodeOutput(
        full_address="test_full_address",
        district="test_district",
        city="test_city",
        street="test_street",
        postcode="123456",
        timezone="UTC+0"
    )

    postcode_mock = mocker.patch(
        "app.service.main.DeliveryService.postcode",
        return_value=postcode_result
    )

    # act
    response = client.post(
        path="/postcode",
        json={
            "address": "test_address"
        }
    )

    # assert
    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.json["full_address"] == postcode_result["full_address"]
    assert response.json["district"] == postcode_result["district"]
    assert response.json["city"] == postcode_result["city"]
    assert response.json["street"] == postcode_result["street"]
    assert response.json["postcode"] == postcode_result["postcode"]
    assert response.json["timezone"] == postcode_result["timezone"]

    postcode_mock.assert_called_once_with(
        data=PostcodeInput(
            address="test_address"
        )
    )


def test_postcode__validation_error__bad_request(client, mocker):

    # arrange
    postcode_mock = mocker.patch(
        "app.service.main.DeliveryService.postcode"
    )

    # act
    response = client.post(
        path="/postcode",
        json={}
    )

    # assert
    assert response.status_code == 400
    assert response.content_type == "application/json"
    postcode_mock.assert_not_called()


def test_postcode__service_exception__internal_server_error(client, mocker):

    # arrange
    postcode_mock = mocker.patch(
        "app.service.main.DeliveryService.postcode",
        side_effect=DadataException(details="test error")
    )

    # act
    response = client.post(
        path="/postcode",
        json={
            "address": "test_address"
        }
    )

    # assert
    assert response.status_code == 500
    assert response.content_type == "application/json"
    postcode_mock.assert_called_once_with(
        data=PostcodeInput(
            address="test_address"
        )
    )

def test_calc__unknown_delivery__bad_request(client, mocker):

    # arrange
    calc_mock = mocker.patch(
        "app.service.main.DeliveryService.calc"
    )

    # act
    response = client.post(
        path="/calc",
        json={
            "type": "WB",
            "width": 10,
            "height": 20,
            "depth": 15,
            "weight": 2.5,
            "is_safe": True
        }
    )

    # assert
    assert response.status_code == 400
    assert response.content_type == "application/json"
    assert "Допустимые перевозчики" in response.json["details"]["type"][0]
    calc_mock.assert_not_called()


def test_calc__non_positive_size__bad_request(client, mocker):

    # arrange
    calc_mock = mocker.patch(
        "app.service.main.DeliveryService.calc"
    )

    # act
    response = client.post(
        path="/calc",
        json={
            "type": "CDEK",
            "width": 0,
            "height": 20,
            "depth": 15,
            "weight": -2.5,
            "is_safe": True
        }
    )

    # assert
    assert response.status_code == 400
    assert response.json["details"]["width"] == ["Значение должно быть больше нуля"]
    assert response.json["details"]["weight"] == ["Значение должно быть больше нуля"]
    calc_mock.assert_not_called()


def test_calc__missing_field__russian_message(client, mocker):

    # arrange
    mocker.patch("app.service.main.DeliveryService.calc")

    # act
    response = client.post(
        path="/calc",
        json={"type": "CDEK", "width": 10}
    )

    # assert
    assert response.status_code == 400
    assert response.json["details"]["weight"] == ["Поле обязательно"]


def test_calc__body_not_object__bad_request(client, mocker):

    # arrange
    mocker.patch("app.service.main.DeliveryService.calc")

    # act
    response = client.post(path="/calc", json=["CDEK", 10])

    # assert
    assert response.status_code == 400
    assert response.json["error"] == "BadRequest"
    assert response.json["details"] == "Тело запроса должно быть объектом JSON."


def test_calc__empty_body__bad_request(client, mocker):

    # arrange
    mocker.patch("app.service.main.DeliveryService.calc")

    # act
    response = client.post(
        path="/calc",
        data="",
        content_type="application/json"
    )

    # assert
    assert response.status_code == 400
    assert response.content_type == "application/json"


def test_calc__wrong_content_type__json_response(client, mocker):

    # arrange
    mocker.patch("app.service.main.DeliveryService.calc")

    # act
    response = client.post(
        path="/calc",
        data="type=CDEK",
        content_type="text/plain"
    )

    # assert
    assert response.status_code == 400
    assert response.content_type == "application/json"
    assert response.json["error"] == "BadRequest"
    assert response.json["details"] == "Тело запроса должно быть объектом JSON."


def test_unknown_route__not_found__json(client):

    # act
    response = client.get(path="/unknown")

    # assert
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert response.json == {"error": "NotFound", "details": "Маршрут не найден."}


def test_wrong_method__method_not_allowed__json(client):

    # act
    response = client.get(path="/calc")

    # assert
    assert response.status_code == 405
    assert response.content_type == "application/json"
    assert response.json["error"] == "MethodNotAllowed"


def test_calc__unexpected_error__internal_server_error(app, client, mocker):

    # arrange
    app.config["PROPAGATE_EXCEPTIONS"] = False
    mocker.patch(
        "app.service.main.DeliveryService.calc",
        side_effect=RuntimeError("внутренний сбой")
    )

    # act
    response = client.post(
        path="/calc",
        json={
            "type": "CDEK",
            "width": 10,
            "height": 20,
            "depth": 15,
            "weight": 2.5,
            "is_safe": True
        }
    )

    # assert
    assert response.status_code == 500
    assert response.content_type == "application/json"
    assert response.json == {
        "error": "InternalServerError",
        "details": "Внутренняя ошибка сервиса."
    }


def test_postcode__dadata_unavailable__json_response(client, mocker):

    # arrange
    postcode_mock = mocker.patch(
        "app.service.main.DeliveryService.postcode",
        side_effect=DadataException()
    )

    # act
    response = client.post(path="/postcode", json={"address": "Москва"})

    # assert
    assert response.status_code == 500
    assert response.content_type == "application/json"
    assert response.json["error"] == "DadataException"
    assert response.json["details"] == messages.MSG_DADATA_UNAVAILABLE
    postcode_mock.assert_called_once_with(data=PostcodeInput(address="Москва"))


def test_postcode__address_not_recognized__bad_request(client, mocker):

    # arrange
    postcode_mock = mocker.patch(
        "app.service.main.DeliveryService.postcode",
        side_effect=AddressNotRecognizedException()
    )

    # act
    response = client.post(path="/postcode", json={"address": "ыыыы"})

    # assert
    assert response.status_code == 400
    assert response.content_type == "application/json"
    assert response.json == {
        "error": "AddressNotRecognizedException",
        "details": messages.MSG_ADDRESS_NOT_RECOGNIZED
    }
    postcode_mock.assert_called_once_with(data=PostcodeInput(address="ыыыы"))
