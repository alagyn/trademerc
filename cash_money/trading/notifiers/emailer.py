import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from .notfier import Notifier, NotifyKeys

from jinja2 import Environment, FileSystemLoader, select_autoescape

class CMEmailer(Notifier):
    def __init__(self, config):
        self._fromAddr = config['SendingEmailAddr']
        self._fromPass = config['SendingEmailPass']
        self._server = config['SMTP_Server']
        self._port = int(config['SMTP_Port'])

        self._toAddr = config['RecievingEmail']


        self.htmlEnv = Environment(
            loader=FileSystemLoader('html_templates'),
            autoescape=select_autoescape()
        )
        self.emailTemplate = self.htmlEnv.get_template("emailtemplate.html")

    def generate(self, portfolio_start, portfolio_cur, portfolio_pl, trades, positions):
        args = {
            NotifyKeys.Portfolio.START: portfolio_start,
            NotifyKeys.Portfolio.CUR: portfolio_cur,
            NotifyKeys.Portfolio.PL: portfolio_pl,
            NotifyKeys.TRADES: trades,
            NotifyKeys.POSITIONS: positions
        }
        return self.emailTemplate.render(
            **args
        )

    def update(self, portfolio_start, portfolio_cur, portfolio_pl, trades, positions):
        content = self.generate(portfolio_start, portfolio_cur, portfolio_pl, trades, positions)

        header = f'Stock Algo Daily Update: {datetime.datetime.today()}'

        self._send(header, content)


    def _send(self, subject: str, content: str):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self._fromAddr
        msg['To'] = self._toAddr

        text = 'Hmmm, supposed to be some HTML here...'
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(content, 'html')

        msg.attach(part1)
        msg.attach(part2)

        s = smtplib.SMTP(self._server, self._port)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self._fromAddr, self._fromPass)

        s.send_message(msg, from_addr=self._fromAddr, to_addrs=self._toAddr)

        s.quit()
