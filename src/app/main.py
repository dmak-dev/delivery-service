from flask import (
    Flask,
    request,
    render_template,
)
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from flasgger import Swagger
from app.service.main import DeliveryService
from app.service import messages
from app.service.exceptions import ServiceException
from app.service.entities import (
    DeliveryOutput,
    PostcodeOutput
)
from app.schema import (
    DeliverySchema,
    PostcodeSchema
)

# Тексты ошибок маршрутизации: у HTTPException они английские по умолчанию.
ROUTING_ERRORS = {
    404: "Маршрут не найден.",
    405: "Метод не поддерживается для этого маршрута.",
    415: "Ожидается тело в формате JSON.",
}

# Служебные тексты marshmallow на русском: остальные ответы сервиса русские.
MARSHMALLOW_MESSAGES = {
    "Missing data for required field.": "Поле обязательно",
    "Not a valid string.": "Ожидается строка",
    "Not a valid number.": "Ожидается число",
    "Not a valid boolean.": "Ожидается логическое значение",
    "Unknown field.": "Неизвестное поле",
    "Invalid input type.": "Ожидается объект JSON",
}


def _translate_details(details):
    """Переводит тексты marshmallow, сохраняя структуру словаря ошибок."""

    if isinstance(details, dict):
        return {key: _translate_details(value) for key, value in details.items()}
    if isinstance(details, list):
        return [_translate_details(item) for item in details]
    return MARSHMALLOW_MESSAGES.get(details, details)


def create_app():

    app = Flask(__name__)
    # Кириллица в ответах читается без экранирования: удобно и в curl, и в Swagger.
    app.json.ensure_ascii = False
    Swagger(app, template={
        "info": {
            "title": "Служба доставки",
            "version": "1.0.0",
            "description": (
                "Сервис считает стоимость доставки по габаритам и весу посылки "
                "и определяет почтовый индекс по адресу."
            ),
        },
    })

    def _error(name: str, details, code: int):
        """Ответ об ошибке: одинаковая форма для всех кодов."""
        return {"error": name, "details": details}, code

    def _get_json_body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return None, _error("BadRequest", messages.MSG_BODY_MUST_BE_OBJECT, 400)
        return data, None

    @app.errorhandler(HTTPException)
    def handle_routing_error(ex):
        """404, 405 и 415 отдаются той же схемой ошибки, а не страницей HTML."""
        details = ROUTING_ERRORS.get(ex.code, ex.description)
        return _error(ex.name.replace(" ", ""), details, ex.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(ex):
        """Необработанная ошибка отдаётся в формате API без подробностей."""
        app.logger.exception("Непредвиденная ошибка: %s", ex)
        return _error("InternalServerError", messages.MSG_INTERNAL_ERROR, 500)

    @app.route("/")
    def template():
        return render_template("base.html")

    @app.route("/calc", methods=["POST"])
    def calculate() -> DeliveryOutput:

        """
        Расчет стоимости доставки
        ---
        tags:
          - Delivery
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [type, width, height, depth, weight, is_safe]
              properties:
                type: {type: string, example: "CDEK"}
                width: {type: number, example: 10.0}
                height: {type: number, example: 20.0}
                depth: {type: number, example: 15.0}
                weight: {type: number, example: 2.5}
                is_safe: {type: boolean, example: true}
        responses:
          200:
            description: Result
            schema:
              type: object
              properties:
                price: {type: number, example: 56.25}
                parcel_type: {type: string, example: "Посылка застрахована. Хрупкий груз!"}
          400:
            description: Ошибка валидации
          500:
            description: Ошибка сервиса
        """

        data, err = _get_json_body()
        if err:
            return err

        service = DeliveryService()
        schema = DeliverySchema()

        try:
            result = service.calc(
                data=schema.load(data)
            )
        except ValidationError as ex:
            return _error("ValidationError", _translate_details(ex.messages), 400)
        except ServiceException as ex:
            return _error(type(ex).__name__, ex.details or ex.message, ex.status_code)
        else:
            return schema.dump(result)

    @app.route("/postcode", methods=["POST"])
    def postcode() -> PostcodeOutput:

        """
        Определение индекса и района по адресу
        ---
        tags:
          - Delivery
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [address]
              properties:
                address: {type: string, example: "Москва, Красная площадь, 1"}
        responses:
          200:
            description: Разобранный адрес
            schema:
              type: object
              properties:
                full_address: {type: string}
                district: {type: string}
                city: {type: string}
                street: {type: string}
                postcode: {type: string}
                timezone: {type: string}
          400:
            description: Ошибка валидации
          500:
            description: Сервис распознавания адресов недоступен
        """

        data, err = _get_json_body()
        if err:
            return err

        schema = PostcodeSchema()
        service = DeliveryService()

        try:
            result = service.postcode(
                data=schema.load(data)
            )
        except ValidationError as ex:
            return _error("ValidationError", _translate_details(ex.messages), 400)
        except ServiceException as ex:
            return _error(type(ex).__name__, ex.details or ex.message, ex.status_code)
        else:
            return schema.dump(result)

    return app


app = create_app()
