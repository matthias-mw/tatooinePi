from datetime import date, datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Klasse für die Abspeicherung der Datenpunkte
from .datapoint import DataPoint

from .alert_chn import AlertChn


# Import Logging Modul
import logging






class Alerting():


    # Serverdaten
    SMTP_SERVER = "smtp.strato.de"
    SMTP_PORT = 587

    # Sender & Empfänger
    EMAIL_SENDER = "info@sv-tatooine.com"
    EMAIL_RECIEVER = "werner.matthias@web.de"

    # Zugangsdaten
    USERNAME = "info@sv-tatooine.com"
    PASSWORD = "0815TaMaPw"
    
    
    
    
    DEBOUNCE_EMAIL_ALARM_S  = 5
    
    DEBOUNCE_EMAIL_BETWEEN_ALARM_S  = 120
    
    EMAIL_LIMIT_PER_DAY = 3
    
    
    
    
    alerts_cfg = []
    
    ALERT_NONE              = 0
    ALERT_PENDING_EMAIL     = 1
    ALERT_PENDING_SMS       = 2
    
    ALERT_CYCLE_RESET   = 0
    ALERT_CYCLE_ACTIVE   = 1
    

    last_email_alarm_send: datetime = datetime.now()
    cnt_email_current_day = 0
    
    email_alarm_activated: bool = False
    
    email_limit_reached: bool = True
    


    def __init__(self, bus = None):
        
        self.conf_alerts()
        
        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        
        pass


    def send_mail(self, current_data_list: list[DataPoint]):


        pass
    
    def conf_alerts(self) -> None:
        
        alert = AlertChn()
        
        alert.name = "T_1W_NO1"
        alert.alert_level = 30
        alert.alert_condition = "gt"
        
        self.alerts_cfg.append(alert)
        
        alert2 = AlertChn()
        alert2.name = "T_1W_NO1"
        alert2.alert_level = 20
        alert2.alert_condition = "st"
        
        self.alerts_cfg.append(alert2)
        
        
        #ToDo
        #print(self.alerts_cfg)
    
        
        
               
        
        
    def calc_alerts(self, current_data_list: list[DataPoint]):
        
        # Für jede Alarmconfiguration        
        for alert in self.alerts_cfg:
            # überprüfe jeden Messkanal, ob er ausgewertet werden muss
            for chn in current_data_list:
                # Wenn der Kanal mit Alarm überwacht wird
                if (chn.name == alert.name):
                    
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # Alarmwert wird erstmalig überschritten
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    if ((alert.alert_condition == "gt") and (chn.value > alert.alert_level) and (alert.alert_cycle == self.ALERT_CYCLE_RESET)):
                        
                        # Abspeichern der Uhrzeit                        
                        alert.alert_time = datetime.now()
                        
                        # Abspeichern Status (E-Mail ist Default)
                        if alert.alert_type == "sms":
                            alert.alert_status = self.ALERT_PENDING_SMS
                        else:
                            alert.alert_status = self.ALERT_PENDING_EMAIL
                        alert.alert_cycle = self.ALERT_CYCLE_ACTIVE
                        
                        # Logging
                        self.logger.info(f"Alarmmeldung: Kanal {alert.name} ist größer {alert.alert_level:3.2f}{alert.unit}")
                        
                        # ToDo
                        print(f"Alarmmeldung: Kanal {alert.name} ist größer {alert.alert_level}{alert.unit}")
                        
                    # Alarmwert Überschreitung wird zurückgesetzt
                    elif ((alert.alert_condition == "gt") and (chn.value < alert.alert_level) and (alert.alert_cycle == self.ALERT_CYCLE_ACTIVE)):

                        # Reset der Alarmbedingung
                        alert.alert_cycle = self.ALERT_CYCLE_RESET
                    
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # Alarmwert wird erstmalig unterschritten      
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    elif ((alert.alert_condition == "st") and (chn.value < alert.alert_level) and (alert.alert_cycle == self.ALERT_CYCLE_RESET)):
                        
                        # Abspeichern der Uhrzeit                        
                        alert.alert_time = datetime.now()
                        
                        # Abspeichern Status (E-Mail ist Default)
                        if alert.alert_type == "sms":
                            alert.alert_status = self.ALERT_PENDING_SMS
                        else:
                            alert.alert_status = self.ALERT_PENDING_EMAIL
                        alert.alert_cycle = self.ALERT_CYCLE_ACTIVE
                        
                        # Logging
                        self.logger.info(f"Alarmmeldung: Kanal {alert.name} ist kleiner {alert.alert_level:3.2f}{alert.unit}")
                        
                        # ToDo
                        print(f"Alarmmeldung: Kanal {alert.name} ist kleiner {alert.alert_level}{alert.unit}")
                        
                    # Alarmwert Unterschreitung wird zurückgesetzt
                    elif ((alert.alert_condition == "st") and (chn.value > alert.alert_level) and (alert.alert_cycle == self.ALERT_CYCLE_ACTIVE)):

                        # Reset der Alarmbedingung
                        alert.alert_cycle = self.ALERT_CYCLE_RESET
            
                    else:
                        
                        pass
                        
    
    def process_alerts(self) -> None:
        
        
        
        # Für jede Alarmconfiguration        
        for alert in self.alerts_cfg:
            
            # Wenn ein Alarm anliegt und eine EMail gesendet werden soll
            if ((alert.alert_status == self.ALERT_PENDING_EMAIL) and 
                (alert.alert_type == "email")):
                
                # Zeit seit Eintritt des Alarms                
                delay = datetime.now() - alert.alert_time
                
                # Debounce E-Mail
                if delay.total_seconds() > self.DEBOUNCE_EMAIL_ALARM_S:
                    
                    # Absenden einer Alarm EMail Notification
                    self.send_email_alert()
            
            
            
    def email_limit(self) -> bool:
        
        aktuellesDatum = date.today().day

        # Wurde an diesem Tag schon mal eine EMail versendet?
        if (aktuellesDatum == self.last_email_alarm_send.day):
            
            # Wenn das EMail Limit noch nicht erreicht wurde
            if (self.cnt_email_current_day < self.EMAIL_LIMIT_PER_DAY):
                # Das Tageslimit an EMails ist noch nicht erreicht
                return False
            else:
                # Das Tageslimit an EMails ist erreicht
                if not(self.email_limit_reached):
                    self.logger.warning('Das Tageslimit für den EMail Versand wurde erreicht.')
                self.email_limit_reached = True
                return True
        else:
            # EMail Tageslimit zurücksetzen
            self.cnt_email_current_day = 0
            self.email_limit_reached = False
        
        # Das Tageslimit an EMails ist noch nicht erreicht
        return False
        
    
    def send_email_alert(self) -> None:
    
        # Betreff & Inhalt Festlegen
        subject = "ALARM Meldung von SV Tatooine"
        body = "Alarmmeldung!\n"
        
        # Für jede Alarmconfiguration        
        for alert in self.alerts_cfg:
            
            # Wenn ein Alarm anliegt und eine EMail gesendet werden soll
            if ((alert.alert_status == self.ALERT_PENDING_EMAIL) and 
                (alert.alert_type == "email")):
                
                # Alarmmeldung erstellen
                body += '\n' + f"Kanal {alert.name} hat die Schwelle von {alert.alert_level:3.2f}{alert.unit} um {alert.alert_time.strftime('%H:%M:%S')}"
                
                # Berücksichtigung der AlarmCondition
                if (alert.alert_condition == "st"):
                    body += " unterschritten!"
                else:
                    body += " überschritten!"
                
                # Alarmmeldung erfolgreich abgeschlossen
                alert.alert_status = self.ALERT_NONE
                
        
        
        
        # Checke das EMail Limit
        if (not(self.email_limit()) and self.email_alarm_activated):           
            
            # EMail Counter hochzählen
            self.cnt_email_current_day += 1
            print(self.cnt_email_current_day)
             
            print(body)

            
            # Message Objekt für die E-Mail
            # später kann an dieses Objekt eine
            # oder mehrere Dateien angehängt
            # werden.
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.EMAIL_SENDER
            msg['To'] = self.EMAIL_RECIEVER
            
            part = MIMEText(body, 'plain')
            msg.attach(part)
            
            
            #ToDo
            
            # Erzeugen einer Mail Session
            smtpObj = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT)
            # Debug Informationen auf der Konsole ausgeben
            smtpObj.set_debuglevel(1)
            # Wenn der Server eine Authentifizierung benötigt dann...
            smtpObj.starttls()
            smtpObj.login(self.USERNAME, self.PASSWORD)
            # absenden der E-Mail
            smtpObj.sendmail(self.EMAIL_SENDER, self.EMAIL_RECIEVER, msg.as_string())
            
        else:
            
            print('Emaillimit erreicht oder Email Unterdrückt')
            
        pass
        
        
            