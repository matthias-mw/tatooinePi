#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Module zur Bearbeitung der Zeitstempel
from datetime import datetime
import email
from pytz import timezone

# Modul für Datenklassen
from dataclasses import dataclass
from dataclasses import field

# Import Logging Modul
import logging

# Festlegen der Zeitzone für die Aufnahme der Messwerte und deren Zeitstempel
tz_berlin = timezone('Europe/Berlin')

@dataclass
class   AlertChn():
    
    name: str = '-'
    """Name des Messkanals"""
    
    unit: str = '-'
    """Masseinheit des Messwertes"""
    
    desc: str = 'desc'
    """Beschreibung der Messkanals"""
    
    alert_level: float = 55555
    
    alert_condition: str = "gt"
    
    alert_type: str = "email"
    
    alert_time: datetime = 0
    
    alert_status: int = 0
    
    alert_cycle: int = 0
    
    last_email_report: datetime = 0
    
    
    
    
    
    
    
    
    