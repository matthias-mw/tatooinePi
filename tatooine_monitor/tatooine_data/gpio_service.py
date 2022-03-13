#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import RaspberryPI GPIOS
import RPi.GPIO as GPIO

# Import Logging Modul
import logging

# Import System Module
import os, signal

class GpioService:
    """Serviceklasse zum Auslesen der GPIOs
    
    In der Klasse sind alle Methoden zum auslesend der GPIOs enthalten.
    Die zu bearbeitenden IOs sind in _GPIO_IN definiert.
    
    Features:
    
    * Limitierung der Anzahl der EMails pro Tag
    
    
    :return:    GPIO_Service Object
    :rtype:     Object
    
    """    
    
    _GPIO_IN = [14,15,17,18,27]
    """Spezifiziert auszulesenden GPIOs, welche als Eingänge definiert werden.
    """
        
    def __init__(self):
         
         
        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        
        # ============================================
        # Konfiguration der IOs
        # ============================================
        GPIO.setmode(GPIO.BCM)
        
        # GPIO Eingänge wählen
        for n in self._GPIO_IN:
            GPIO.setup(n, GPIO.IN)
            
    def getGPIO(self, io: int) -> bool:
        """Ausgabe des aktuellen Wertes eines GPIOs
        
        Die Funktion gibt den aktuellen Wert eines GPIOs zurück. Der entsprechende Kanal wird durch "io" spezifiziert.

        :param io: Kanalnummer
        :type io: int
        :return: Wert des IO
        :rtype: bool
        """
        
        # Wert ausgeben, wenn der IO ein Input ist
        for i in self._GPIO_IN:
            if i == io:
                return GPIO.input(io)
        
        # Programmabbruch, falls ein falscher Kanal spezifiziert wurde
        self.logger.critical(f"GPIO Kanal {io} ist nicht für das Auslesen spezifiziert. Bitte Config überprüfen!")
        
        print(f"GPIO Kanal {io} ist nicht für das Auslesen spezifiziert. Bitte Config überprüfen!")
        print("Programm  wird beendet ...")
                
        # Program beenden aus einem Tread heraus geht nur in Linux
        os.kill(os.getpid(), signal.SIGINT)


        return None