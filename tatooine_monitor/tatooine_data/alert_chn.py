#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Module zur Bearbeitung der Zeitstempel
from datetime import datetime

# Modul für Datenklassen
from dataclasses import dataclass
from dataclasses import field
@dataclass
class   AlertChn():
    """Datenobjekt, welches die Konfiguration eines Alarms enthält
    
    Das Dataclass-Datenobjekt enthält alle Einstellungen für einen definierten 
    Alarm. Neben den Einstellungen die über :mod:`~tatooine_data.alert_service.Alerting.alerts_cfg` aus der Konfigurationsdatei ausgelesen werden, sind 
    auch Steuerungsinformationen enthalten, welche den aktuellen Zustand des 
    Alarms beschreiben.
    """
    
    name: str = '-'
    """Name des Messkanals der zu Überwachen ist"""
    
    unit: str = '-'
    """Einheit des Messwertes"""
    
    desc: str = 'desc'
    """Beschreibung des Alarms"""
    
    level: float = 55555
    """Schwellwert für die Überwachung des Kanals"""
    
    hysterese_level: float = 1
    """Wert der Hysterese, um die Auslösung an der Alarmschwelle zu entprellen"""
    
    condition: str = "gt"
    """Art der Überwachung der Schwelle (gt = greater then; lt = lower then)"""
    
    type: str = "email"
    """Art der Alarmmeldung (email, sms)"""
    
    time: datetime = 0
    """Zeitstempel der Alarmauslösung"""
    
    status: int = 0
    """Status dieses Alarms :mod:`~tatooine_data.alert_service.Alerting.ALERT_NONE` :mod:`~tatooine_data.alert_service.Alerting.ALERT_PENDING_EMAIL` :mod:`~tatooine_data.alert_service.Alerting.ALERT_PENDING_SMS` """
    
    cycle: int = 0
    """Status des aktuellem Alarmzyklus :mod:`~tatooine_data.alert_service.Alerting.ALERT_CYCLE_ACTIVE` wird erst zurückgenommen, wenn die Schwelle um mindestens die Hysteres wieder unter-/überschritten wurde."""
    
    last_email_report: datetime = 0
    """Zeitstempel des letzten E-Mail Report"""
    
    
    
    
    
    
    
    