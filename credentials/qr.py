import base64
from io import BytesIO

import qrcode
from qrcode.image.svg import SvgPathImage


def qr_svg_data(code):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(code)
    qr.make(fit=True)
    image = qr.make_image(image_factory=SvgPathImage)
    output = BytesIO()
    image.save(output)
    encoded = base64.b64encode(output.getvalue()).decode('ascii')
    return f'data:image/svg+xml;base64,{encoded}'
