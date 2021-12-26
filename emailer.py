import smtplib
from email.message import EmailMessage
from typing import Dict


class CMEmailer:
    def __init__(self, config: Dict[str, str]):
        self._fromAddr = config['LOG_EMAIL_ADDR']
        self._fromPass = config['LOG_EMAIL_PASS']
        self._server = config['EMAIL_SERVER']
        self._port = int(config['EMAIL_PORT'])

        self._toAddr = config['RECIEVING_ADDR']

        print(f'"{self._fromAddr}"')
        print(f'"{self._fromPass}"')

    def send(self, subject: str, content: str):
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = subject
        msg['From'] = self._fromAddr
        msg['To'] = self._toAddr

        s = smtplib.SMTP(self._server, self._port)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self._fromAddr, self._fromPass)

        s.send_message(msg, from_addr=self._fromAddr, to_addrs=self._toAddr)

        s.quit()
