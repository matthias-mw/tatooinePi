#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modul zur Bearbeitung der Zeitstempel
from datetime import date, datetime

# Modul zur Verarbeitung von CSV Dateien
import csv
import sys

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

# Config Files auswerten
from configparser import ConfigParser

# Hilfsfunktionen
from .helper import *


class Alerting:
    """Benachrichtigungssystem von TatooineMonitor
    
    In der Klasse sind alle Funktionen, welche zum Aussenden von Alarm- oder Statusmeldungen benötigt werden, enthalten. Es ist vorgesehen die Benachrichtigungen über E-Mail oder SMS (tbd) zu versenden.
    
    Features:
    
    * Limitierung der Anzahl der EMails pro Tag
    
    
    :return:    AlertingObjekt
    :rtype:     Object
    
    """

    __SMTP_SERVER = ""
    """Adresse des SMTP Servers für die E-Mailaustausch """
    __SMTP_PORT = 587
    """Port des SMTP Servers für die E-Mailaustausch """

    __EMAIL_SENDER = ""
    """Absender Adresse für die E-Mails"""
    __EMAIL_RECIEVER = ""
    """Empfängeradresse für die E-Mails"""

    # SMTP Zugangsdaten (__SMTP_USERNAME/__SMTP_PASSWORD) werden in __init__
    # aus .env/Umgebung gelesen (SMTP_USERNAME, SMTP_PASSWORD) - nicht im Code!

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
    
    DEFAULT_CONF_DIR = "/opt/tatooinePi/tatooine_monitor"
    """Standard-Verzeichnis der Konfigurationsdateien"""


    def __init__(self, conf: ConfigParser, conf_dir: str = DEFAULT_CONF_DIR):

        # config_alerts.csv liegt im selben Verzeichnis wie die conf
        self.CONF_FILE = os.path.join(conf_dir, "config_alerts.csv")

        # ============================================
        # Einstellungen aus confFile übernehmen
        # ============================================
        self.__SMTP_SERVER = helper.getConfigValue(conf,"ALERTING","SMTP_SERVER")
        self.__SMTP_PORT = int(helper.getConfigValue(conf,"ALERTING","SMTP_PORT"))
        self.__EMAIL_SENDER = helper.getConfigValue(conf,"ALERTING","EMAIL_SENDER")
        self.__EMAIL_RECIEVER = helper.getConfigValue(conf,"ALERTING","EMAIL_RECIEVER")
        self.DEBOUNCE_EMAIL_ALARM_S = int(helper.getConfigValue(conf,\
            "ALERTING","DEBOUNCE_EMAIL_ALARM_S"))
        self.DEBOUNCE_EMAIL_BETWEEN_ALARM_S = int(helper.getConfigValue(conf,\
            "ALERTING", "DEBOUNCE_EMAIL_BETWEEN_ALARM_S"))
        self.EMAIL_LIMIT_PER_DAY = int(helper.getConfigValue(conf,"ALERTING",\
            "EMAIL_LIMIT_PER_DAY"))

        # SMTP Zugangsdaten kommen aus .env/Umgebung (nicht im Repo!)
        self.__SMTP_USERNAME = helper.get_secret("SMTP_USERNAME")
        self.__SMTP_PASSWORD = helper.get_secret("SMTP_PASSWORD")


        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

        # Konfiguration der Alarme einlesen
        self.conf_alerts()
        
    
    def conf_alerts(self) -> None:
        """Konfiguration aller Messkanäle
        
        Zu Beginn des Programms wird die Datei :file:`config_alerts.csv` gelesen. 
        In Ihr sind alle relevanten Alarme zeilenweise aufgeführt. So
        werden alle Parameter in die :mod:`~tatooine_data.alert_service.Alerting.alerts_cfg` eingelesen und anschließend in der Funktion :mod:`~tatooine_data.alert_service.Alerting.calc_alerts` genutzt.
        Es werden folgenden Spalten benötigt:
        
        .. code-block:: text
        
            Name, Unit, Description, Level, Hysterese, Condition, Type
           
        Können die Kanäle nicht eingelesen werden, wird das Programm beendet.
        
        """    
        
        if not os.path.isfile(self.CONF_FILE):
            print(f"FEHLER: Alarmkonfiguration nicht gefunden: {self.CONF_FILE}")
            sys.exit(1)

        # Sicheres öffnen der CSV Datei, welche durch With automatisch
        # nach Beendigung des Auslesen geschlossen wird
        with open(self.CONF_FILE) as csvdatei:
            
            # Auslesen der Daten aus der CSV
            csv_reader_object = csv.reader(csvdatei)
            line_count = 0
            header = []
            
            # Verarbeiten der Daten aus der CSV Zeile für Zeile
            for row in csv_reader_object:
                # Die erste Zeile der CSV repäsentiert die Header
                if line_count == 0:
                    header = [colum for colum in row]
                    line_count +=1
                # Zuordnen der Config eines jeden Kanals in ein Dictonary
                else:
                    i=0
                    channel_conf = {}
                    for y in header:
                        channel_conf[y] = row[i]
                        i +=1

                    # Auswerten der Konfig Daten aus der CSV
                    try:
                        alert = AlertChn()
                        alert.name = channel_conf['Name']
                        alert.unit = channel_conf['Unit']
                        alert.desc = channel_conf['Description']
                        alert.level = float(channel_conf['Level'])
                        alert.hysterese_level = float(channel_conf['Hysterese'])
                        alert.condition  = channel_conf['Condition']
                        alert.type  = channel_conf['Type']
                        
                        # in der Liste der Alarme abspeichern
                        self.alerts_cfg.append(alert)
                        self.logger.info(f"Alarm konfiguriert: {alert.name}( {alert.unit}), {alert.level} +/-{alert.hysterese_level} , {alert.condition}")
                        
                    # Programm beenden sollte das Auslesen schief gehen
                    except:

                        self.logger.critical(f"Fehler in der Konfigurationsdatei für die Alarmmeldungen {self.CONF_FILE}. Es werden folgende Spaltenheader erwartet: Name, Unit, Description, Level, Hysterese, Condition, Type")
                        
                        print(f"Fehler in der Konfigurationsdatei für die Alarmmeldungen {self.CONF_FILE}\nEs werden folgende Spaltenheader erwartet:\nName, Unit, Description, Level, Hysterese, Condition, Type")
                        
                        print(header)
                        # beendet das Programm
                        sys.exit("Programm wird beendet wegen falscher Alert Config...") 


    def calc_alerts(self, current_data_list: list[DataPoint]) -> None:
        """Berechnung der anliegenden Alarme
             
        Diese Funktion analysiert alle Alarmkonfigurationen in 
        :mod:`~tatooine_data.alert_service.Alerting.alerts_cfg` und vergleicht
        anhand der aktuellen Messdaten, ob der jeweilige Alarm ausgelöst werden muss. Abhängig von dem Alarmtyp  :mod:`~tatooine_data.alert_chn.Alert_Chn.type` werden verschieden Aktionen ausgelöst.

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
                    if ((alert.condition == "gt") and (chn.value > alert.level) and (alert.cycle == self.ALERT_CYCLE_RESET)):
                        
                        # Abspeichern der Uhrzeit                        
                        alert.time = datetime.now()
                        
                        # Abspeichern Status (E-Mail ist Default)
                        if alert.type == "sms":
                            alert.status = self.ALERT_PENDING_SMS
                        else:
                            alert.status = self.ALERT_PENDING_EMAIL
                        alert.cycle = self.ALERT_CYCLE_ACTIVE
                        
                        # Logging
                        self.logger.info(f"Alarmmeldung: Kanal {alert.name} ist größer {alert.level:3.2f}{alert.unit}")
                        
                    # Alarmwert Überschreitung wird zurückgesetzt
                    # (erst wenn die Hysterese komplett unterschritten ist)
                    elif ((alert.condition == "gt") and (chn.value < alert.level - alert.hysterese_level) and (alert.cycle == self.ALERT_CYCLE_ACTIVE)):

                        # Reset der Alarmbedingung
                        alert.cycle = self.ALERT_CYCLE_RESET
                        self.logger.info(f"Alarm zurückgesetzt: Kanal {alert.name} ist unter {alert.level - alert.hysterese_level:3.2f}{alert.unit}")
                    
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # Alarmwert wird erstmalig unterschritten      
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    elif ((alert.condition == "st") and (chn.value < alert.level) and (alert.cycle == self.ALERT_CYCLE_RESET)):
                        
                        # Abspeichern der Uhrzeit                        
                        alert.time = datetime.now()
                        
                        # Abspeichern Status (E-Mail ist Default)
                        if alert.type == "sms":
                            alert.status = self.ALERT_PENDING_SMS
                        else:
                            alert.status = self.ALERT_PENDING_EMAIL
                        alert.cycle = self.ALERT_CYCLE_ACTIVE
                        
                        # Logging
                        self.logger.info(f"Alarmmeldung: Kanal {alert.name} ist kleiner {alert.level:3.2f}{alert.unit}")
                       
                        
                    # Alarmwert Unterschreitung wird zurückgesetzt
                    # (erst wenn die Hysterese komplett überschritten ist)
                    elif ((alert.condition == "st") and (chn.value > alert.level + alert.hysterese_level) and (alert.cycle == self.ALERT_CYCLE_ACTIVE)):

                        # Reset der Alarmbedingung
                        alert.cycle = self.ALERT_CYCLE_RESET
                        self.logger.info(f"Alarm zurückgesetzt: Kanal {alert.name} ist über {alert.level + alert.hysterese_level:3.2f}{alert.unit}")
            
                    else:
                        
                        pass
                        
    
    def process_alerts(self, current_data_list: list[DataPoint]) -> None:
        """Verarbeiten von allen Alarmkonfigurationen

        Diese Funktion verarbeitet alle durch 
        :mod:`~tatooine_data.alert_service.Alerting.calc_alerts` ermittelten aktiven Alarme. Abhängig von dem Alarmtyp  :mod:`~tatooine_data.alert_chn.Alert_Chn.type` werden verschieden Aktionen ausgelöst.

        :param current_data_list: Array der aktuellen Messdaten
        :type current_data_list: list[DataPoint]
        """
        
        
        # Für jede Alarmconfiguration        
        for alert in self.alerts_cfg:
            
            # Wenn ein Alarm anliegt und eine EMail gesendet werden soll
            if ((alert.status == self.ALERT_PENDING_EMAIL) and 
                (alert.type == "email")):
                
                # Zeit seit Eintritt des Alarms                
                delay = datetime.now() - alert.time
                
                # Debounce E-Mail
                if delay.total_seconds() > self.DEBOUNCE_EMAIL_ALARM_S:
                    
                    # Absenden einer Alarm EMail Notification
                    self.send_email_alert(current_data_list)
            
            
            
    def email_limit(self) -> bool:
        """Check ob das aktuelle E-Mail Limit erreicht wurde
        
        Die Funktion checkt, ob die Anzahl der pro Tag zulässigen E-Mails
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
            smtpObj.login(self.__SMTP_USERNAME, self.__SMTP_PASSWORD)
            # absenden der E-Mail
            smtpObj.sendmail(self.__EMAIL_SENDER, self.__EMAIL_RECIEVER, msg.as_string())

            self.logger.info(f"Alarm-EMail versendet.")
            self.logger.debug(f"Alarm-EMail Config: {self.__SMTP_SERVER} {self.__SMTP_PORT} {msg['To']} -> {txt}")

    def send_test_email(self) -> None:
        """Versendet eine Test-Alarm-E-Mail

        Sendet eine einzelne Test-E-Mail über den konfigurierten SMTP-Server,
        unabhängig vom E-Mail-Tageslimit und Debouncing (z.B. zum Prüfen der
        Zugangsdaten via -t/--testemail).

        :raises Exception: wenn der Versand fehlschlägt
        """

        subject = "TEST-Alarm: TatooineMonitor"
        body = ("<!DOCTYPE html><html><body>"
                "<h2>Test-Alarmmeldung</h2>"
                "<p>Dies ist eine Test-E-Mail des TatooineMonitor (ausgelöst über "
                "-t/--testemail). Wenn du diese Mail erhältst, funktioniert der "
                "SMTP-Versand inklusive Zugangsdaten.</p>"
                "</body></html>")

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.__EMAIL_SENDER
        msg['To'] = self.__EMAIL_RECIEVER
        msg.attach(MIMEText(body, 'html'))

        smtpObj = smtplib.SMTP(self.__SMTP_SERVER, self.__SMTP_PORT)
        smtpObj.starttls()
        smtpObj.login(self.__SMTP_USERNAME, self.__SMTP_PASSWORD)
        smtpObj.sendmail(self.__EMAIL_SENDER, self.__EMAIL_RECIEVER, msg.as_string())
        smtpObj.quit()

        self.logger.info(f"Test-Alarm-E-Mail versendet an {self.__EMAIL_RECIEVER}")
        print("Test-Alarm-E-Mail versendet an " + self.__EMAIL_RECIEVER)

    def msg_html(self, current_data_list: list[DataPoint], add_text: str) -> str:
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
            if (alert.status == self.ALERT_PENDING_EMAIL):
                
                # Alarmmeldung erstellen
                body += f"<h3>Kanal {alert.name} hat die Schwelle von {alert.level:3.2f}{alert.unit} um {alert.time.strftime('%H:%M:%S')}"
                
                # Berücksichtigung der AlarmCondition
                if (alert.condition == "st"):
                    body += " unterschritten!</h3>"
                else:
                    body += " überschritten!</h3>"
                
                # Alarmmeldung erfolgreich abgeschlossen
                alert.status = self.ALERT_NONE
        
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






            