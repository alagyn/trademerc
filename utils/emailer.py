import smtplib
from email.message import EmailMessage


# TODO https://stackoverflow.com/questions/882712/sending-html-email-using-python

class CMEmailer:
    def __init__(self, config):
        self._fromAddr = config['SendingEmailAddr']
        self._fromPass = config['SendingEmailPass']
        self._server = config['SMTP_Server']
        self._port = int(config['SMTP_Port'])

        self._toAddr = config['RecievingEmail']

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
