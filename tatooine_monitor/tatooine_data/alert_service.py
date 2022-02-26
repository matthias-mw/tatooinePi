#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modul zur Bearbeitung der Zeitstempel
from ast import Str
from datetime import date, datetime

# Module für das Versenden von E-Mails
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Helper Modul stell Kanalkonfiguration zur Verfügung
from tatooine_data import helper

# Klasse für die Abspeicherung der Datenpunkte
from .datapoint import DataPoint

# Klasse für die Alarmkonfigurationen
from .alert_chn import AlertChn

# Import Logging Modul
import logging


class Alerting:
    """Benachrichtigungssystem von TatooineMonitor
    
    In der Klasse sind alle Funktionen, welche zum Aussenden von Alarm- oder Statusmeldungen benötigt werden, enthalten. Es ist vorgesehen die Benachrichtigungen über E-Mail oder SMS (tbd) zu versenden.
    
    Features:
    
    * Limitierung der Anzahl der EMails pro Tag
    
    
    :return:    AlertingObjekt
    :rtype:     Object
    
    """


    __SMTP_SERVER = "smtp.strato.de"
    """Adresse des SMTP Servers für die E-Mailaustausch """
    __SMTP_PORT = 587
    """Port des SMTP Servers für die E-Mailaustausch """

    __EMAIL_SENDER = "info@sv-tatooine.com"
    """Absender Adresse für die E-Mails"""
    __EMAIL_RECIEVER = "werner.matthias@web.de"
    """Empfängeradresse für die E-Mails"""

    #ToDo Daten verschlüsseln
    __USERNAME = "info@sv-tatooine.com"
    """Benutzername für den Zugang zum E-Mail Provider"""
    __PASSWORD = "0815TaMaPw"
    """Benutzerkennwort für den Zugang zum E-Mail Provider"""
    
    DEBOUNCE_EMAIL_ALARM_S  = 5
    """Zeitverzögerung nach dem Auftreten des Alarms, bis die E-Mail 
    versendet wird. Damit soll die Chance eingeräumt werden ggf noch 
    andere Alarme in der gleichen E-Mal zu versenden"""
    
    DEBOUNCE_EMAIL_BETWEEN_ALARM_S  = 120
    """Mindest Zeitverzögerung bis zum erneuten versenden einer E-Mail. So soll verhindert werden, dass E-Mails zu häufig versendet werden."""
    
    EMAIL_LIMIT_PER_DAY = 3
    """Maximal Anzahl von E-Mails pro Tag. So wird verhindert, dass bei einer Fehlfunktion zu viele E-Mails versendet werden"""
    
    ALERT_NONE              = 0
    """Statusgröße für :mod:`~tatooine_data.alert_chn.AlertChn`  -> kein unbearbeiteter Alarm liegt vor"""
    
    ALERT_PENDING_EMAIL     = 1
    """Statusgröße für :mod:`~tatooine_data.alert_chn.AlertChn`   -> Alarm liegt vor und wartet auf E-Mail Versand"""
    
    ALERT_PENDING_SMS       = 2
    """Statusgröße für :mod:`~tatooine_data.alert_chn.AlertChn`   -> Alarm liegt vor und wartet auf SMS Versand"""
    
    ALERT_CYCLE_RESET   = 0
    """Statusgröße für :mod:`~tatooine_data.alert_chn.AlertChn`   -> Alarm hat den Grenzwert nicht verletzt und wird zurückgenommen"""
    
    ALERT_CYCLE_ACTIVE   = 1
    """Statusgröße für :mod:`~tatooine_data.alert_chn.AlertChn`   -> Alarm hat den Grenzwert verletzt"""
    
    alerts_cfg = []
    """Konfiguration der Alarme"""
    
    _last_email_alarm_send: datetime = datetime.now()
    """Zeitpunkt zudem zuletzt einen E-Mail versendet wurde."""
    
    _cnt_email_current_day = 0
    """Anzahl von versendeten E-Mails am aktuellem Tag"""
    
    _email_alarm_activated: bool = True
    """Aktiviertung der E-Mail Alarmfunktion (false unterdrückt das Versenden von -Mails"""
    _email_limit_reached: bool = False
    """True: die zulässige maximale Anzahl von Mails wurde bereits verendet"""
    


    def __init__(self, bus = None):
        
        self.conf_alerts()
        
        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        
        pass

    
    def conf_alerts(self) -> None:
        
        alert = AlertChn()
        
        alert.name = "T_1W_NO1"
        alert.alert_level = 42
        alert.alert_condition = "gt"
        
        self.alerts_cfg.append(alert)
        
        alert2 = AlertChn()
        alert2.name = "T_1W_NO1"
        alert2.alert_level = 32
        alert2.alert_condition = "st"
        
        self.alerts_cfg.append(alert2)
        
        
        #ToDo
        #print(self.alerts_cfg)
    
        
        
               
        
        
    def calc_alerts(self, current_data_list: list[DataPoint]) -> None:
        """Berechnung der anliegenden Alarme
             
        Diese Funktion analysiert alle Alarmkonfigurationen in 
        :mod:`~tatooine_data.alert_service.Alerting.alerts_cfg` und vergleicht
        anhand der aktuellen Messdaten, ob der jeweilige Alarm ausgelöst werden muss. Abhängig von dem Alarmtyp  :mod:`~tatooine_data.alert_chn.Alert_Chn.alert_type` werden verschieden Aktionen ausgelöst.

        :param current_data_list: Array der aktuellen Messdaten
        :type current_data_list: list[DataPoint]
        """
        
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
                        
    
    def process_alerts(self, current_data_list: list[DataPoint]) -> None:
        """Verarbeiten von allen Alarmkonfigurationen

        Diese Funktion verarbeitet alle durch 
        :mod:`~tatooine_data.alert_service.Alerting.calc_alerts` ermittelten aktiven Alarme. Abhängig von dem Alarmtyp  :mod:`~tatooine_data.alert_chn.Alert_Chn.alert_type` werden verschieden Aktionen ausgelöst.

        :param current_data_list: Array der aktuellen Messdaten
        :type current_data_list: list[DataPoint]
        """
        
        
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
                    self.send_email_alert(current_data_list)
            
            
            
    def email_limit(self) -> bool:
        """Check ob das aktuelle E-Mail Limit erreicht wurde
        
        Die Funktion checkz ob die Anzahl der pro Tag zulässigen E-Mails
        :class:`~tatooine_data.alert_service.Alerting.EMAIL_LIMIT_PER_DAY` 
        bereits versendet wurde.

        :return: True: Limit wurde erreicht
        :rtype: bool
        """
        
        aktuellesDatum = date.today().day

        # Wurde an diesem Tag schon mal eine EMail versendet?
        if (aktuellesDatum == self._last_email_alarm_send.day):
            
            # Wenn das EMail Limit noch nicht erreicht wurde
            if (self._cnt_email_current_day < self.EMAIL_LIMIT_PER_DAY):
                # Das Tageslimit an EMails ist noch nicht erreicht
                return False
            else:
                # Das Tageslimit an EMails ist erreicht
                if not(self._email_limit_reached):
                    self.logger.warning('Das Tageslimit für den EMail Versand wurde erreicht.')
                self._email_limit_reached = True
                return True
        else:
            # EMail Tageslimit zurücksetzen
            self._cnt_email_current_day = 0
            self._email_limit_reached = False
        
        # Das Tageslimit an EMails ist noch nicht erreicht
        return False
        
    
    def send_email_alert(self, current_data_list: list[DataPoint]) -> None:
        """Aussenden einer E-Mail Alarmmeldung
        
        Die Funktion erstellt eine Alarmmeldung, welche dann per E-Mail
        versendet wird. Die EMail wird im HTML Format versendet.

        :param current_data_list: Liste der aktuellen Messwerte
        :type current_data_list: list[DataPoint]
        """
        
        # Checke das EMail Limit
        if (not(self.email_limit()) and self._email_alarm_activated):           
            # E-Mail Counter hochzählen
            self._cnt_email_current_day += 1
            self._last_email_alarm_send = datetime.now()
            
            # Betreff & Inhalt Festlegen
            subject = "ALARM Meldung von SV Tatooine"
            # Zusatztext unter der Datentabelle
            txt = f"E-Mail Nr {self._cnt_email_current_day:d} am heutigen Tag"
            # Meldungstext erstellen
            body = self.msg_html(current_data_list,txt)
            part = MIMEText(body, 'html')
            
            self.logger.debug(f'Email per Day Count:{self._cnt_email_current_day}')
            
            # Message Objekt für die E-Mail
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.__EMAIL_SENDER
            msg['To'] = self.__EMAIL_RECIEVER
            msg.attach(part)

            # Erzeugen einer Mail Session
            smtpObj = smtplib.SMTP(self.__SMTP_SERVER, self.__SMTP_PORT)
            # Debug Informationen auf der Konsole ausgeben
            smtpObj.set_debuglevel(0)
            # Wenn der Server eine Authentifizierung benötigt dann...
            smtpObj.starttls()
            smtpObj.login(self.__USERNAME, self.__PASSWORD)
            # absenden der E-Mail
            smtpObj.sendmail(self.__EMAIL_SENDER, self.__EMAIL_RECIEVER, msg.as_string())
            

            
        else:
            
            self.logger.debug(f'Emaillimit erreicht oder Email Unterdrückt, Alarm NR {self._cnt_email_current_day}')
            
        pass
        
        
    def msg_html(self, current_data_list: list[DataPoint], add_text: str) -> Str:
        """Erstellung einer Alarmmeldung in HTML Format
        
        Diese Funktion erstellt eine Alarmmeldung im HTML Format. Dabei wird 
        der Kanal ausgegeben, welcher den den Alarm ausgelöst hat und welcher 
        der Schwellen verletzt wurde. Zusätzlich werden alle aktuellen 
        Messwerte ausgegeben.

        .. code-block:: html
        
            <html>
            <body>
            <h2>Alarmmeldung! </h2>
            <h3>Kanal T_1W_NO4 hat die Schwelle von 42.00- um 12:51:08 überschritten! </h3>

            <table style="width:50%">
            <tr>
                <th align ="left">Channel</th>
                <th align ="right">Value</th>
            </tr>
            <tr>
                <td>U_Service</td>
                <td align ="right">11.90V</td>
            </tr>
            <tr>
                <td>U_Bowtruster</td>
                <td align ="right">11.20V</td>
            </tr>
            </table>

            <p>Tabellen Unterschrift ....</p>

            </body>
            </html>


        :param current_data_list: Liste der aktuellen Messwerte
        :type current_data_list: list[DataPoint]
        :param add_text: Zusätzlicher Text, der unter der Messwerttabelle steht
        :type add_text: str
        :return: gesamter Messagetext im HTML Format
        :rtype: Str
        """
        
        # Header für HTML Message
        body = "<!DOCTYPE html><html><body><h2>Alarmmeldung!</h2>"
        
        # Für jede Alarmconfiguration        
        for alert in self.alerts_cfg:
            
            # Wenn ein Alarm anliegt und eine EMail gesendet werden soll
            if (alert.alert_status == self.ALERT_PENDING_EMAIL):
                
                # Alarmmeldung erstellen
                body += f"<h3>Kanal {alert.name} hat die Schwelle von {alert.alert_level:3.2f}{alert.unit} um {alert.alert_time.strftime('%H:%M:%S')}"
                
                # Berücksichtigung der AlarmCondition
                if (alert.alert_condition == "st"):
                    body += " unterschritten!"
                else:
                    body += " überschritten!"
                
                # Alarmmeldung erfolgreich abgeschlossen
                alert.alert_status = self.ALERT_NONE

        body +="</h3>"
        
        # Alle aktuellen MEsswerte anhängen
        # Tabellenkopf
        body +="<table style='width:50%'><tr><th align ='left'>Channel</th><th align ='right'>Value</th></tr>"
        
        # Datenzeilen 
        for x in current_data_list:
            body += "<tr><td>" + x.name + "</td><td align ='right'>" + \
                f"{x.value:0.2f}{x.unit}" + "</td></tr>"            
        body += "</table>"

        # Text unter der Tabelle
        body += "<p>" + add_text + "</p></body></html>"
        
        return body






            