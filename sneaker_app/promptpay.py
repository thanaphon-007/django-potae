"""สร้าง PromptPay QR ตามมาตรฐาน EMVCo (สแกนจ่ายผ่านแอปธนาคารไทยได้)"""
import base64
import io


def _crc16_ccitt(data):
    crc = 0xFFFF
    for ch in data:
        crc ^= ord(ch) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, '04X')


def _field(tag, value):
    return '{}{:02d}{}'.format(tag, len(value), value)


def _digits_only(value):
    return ''.join(ch for ch in str(value or '') if ch.isdigit())


def normalize_target(target):
    """แปลงพร้อมเพย์ไอดีเป็น (subtag, value) หรือ (None, None) ถ้าไอดีไม่ถูกต้อง

    รองรับ: เบอร์โทร 10 หลัก (ขึ้นต้น 0), เบอร์โทร 11 หลัก (ขึ้นต้น 66),
    เลขบัตรประชาชน 13 หลัก และ e-Wallet 15 หลัก
    """
    digits = _digits_only(target)
    if len(digits) == 13:
        return '02', digits
    if len(digits) == 15:
        return '03', digits
    if len(digits) == 10 and digits.startswith('0'):
        return '01', '0066' + digits[1:]
    if len(digits) == 11 and digits.startswith('66'):
        return '01', '00' + digits
    return None, None


def validate_target(target):
    """คืนข้อความ error (str) หรือ None ถ้าพร้อมเพย์ไอดีถูกต้อง"""
    digits = _digits_only(target)
    if not digits:
        return 'ยังไม่ได้ตั้งค่าพร้อมเพย์ไอดี'
    if normalize_target(digits)[0] is not None:
        return None
    return ('พร้อมเพย์ไอดีไม่ถูกต้อง ต้องเป็นเบอร์โทร 10 หลัก, '
            'เลขบัตรประชาชน 13 หลัก หรือ e-Wallet 15 หลัก (ค่าปัจจุบัน {} หลัก)').format(len(digits))


def generate_promptpay_payload(target, amount=None):
    """คืนค่า payload string สำหรับสร้าง QR หรือ '' ถ้าไอดีไม่ถูกต้อง"""
    tag, value = normalize_target(target)
    if tag is None:
        return ''

    merchant = _field('00', 'A000000677010111') + _field(tag, value)

    payload = _field('00', '01')
    payload += _field('01', '12' if amount else '11')
    payload += _field('29', merchant)
    payload += _field('53', '764')
    if amount:
        payload += _field('54', '{:.2f}'.format(float(amount)))
    payload += _field('58', 'TH')
    payload += '6304'

    return payload + _crc16_ccitt(payload)


def generate_qr_data_uri(payload):
    """สร้างรูป QR จาก payload เป็น data URI (PNG base64) หรือ '' ถ้าสร้างไม่ได้"""
    if not payload:
        return ''
    import qrcode
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return 'data:image/png;base64,' + encoded
