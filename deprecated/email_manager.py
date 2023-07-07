from typing import Mapping, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread
import smtplib

# TODO make the receiving address not be singular


class _EmailManager:

    def __init__(self, fromAddr, fromPass, server, port, toAddr) -> None:
        self._fromAddr = fromAddr
        self._fromPass = fromPass
        self._server = server
        self._port = port
        self._toAddr = toAddr


_manager: Optional[_EmailManager] = None


def setupEmailManager(config: Mapping[str, str]):
    fromAddr = config['SendingEmailAddr']
    fromPass = config['SendingEmailPass']
    server = config['SMTP_Server']
    port = int(config['SMTP_Port'])
    toAddr = config['RecievingEmail']
    global _manager
    _manager = _EmailManager(fromAddr, fromPass, server, port, toAddr)


def _send_thread(msg: MIMEMultipart):
    if _manager is None:
        return

    s = smtplib.SMTP(_manager._server, _manager._port)
    s.starttls()
    s.login(_manager._fromAddr, _manager._fromPass)

    s.send_message(
        msg, from_addr=_manager._fromAddr, to_addrs=_manager._toAddr
    )

    s.quit()


def sendEmail(
    subject: str,
    *,
    content_html: Optional[str] = None,
    content_text: str = ""
):
    if _manager is None:
        raise RuntimeError("send_email(): Manager not setup")

    msg = MIMEMultipart('alternative')
    if content_html is not None:
        msg.attach(MIMEText(content_html, "html"))

    msg.attach(MIMEText(content_text, "plain"))

    msg['Subject'] = subject
    msg['From'] = _manager._fromAddr
    msg['To'] = _manager._toAddr

    Thread(target=_send_thread, args=(msg, ), daemon=False).start()
