class Delivery:

    CDEK = 'CDEK'
    BX = 'Boxberry'
    PR = "Почта России"
    AMZ = "Amazon Delivery"
    CP = "Canada Post"
    DHL = "DHL Post"

    DOMESTIC = CDEK, BX, PR
    INTERNATIONAL = AMZ, CP, DHL

    CHOICES = (
        (CDEK, CDEK),
        (BX, BX),
        (PR, PR),
        (AMZ, AMZ),
        (CP, CP),
        (DHL, DHL)
    )

    VALUES = (CDEK, BX, PR, AMZ, CP, DHL)