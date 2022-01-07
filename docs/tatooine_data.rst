Python Package zur Messdatenerfassung
=====================================

In diesem Package sind alle Module zu Erfassung, Berechnung und Speicherung von den Messdaten  des TatooineMonitor enthalten.


Datenerfassung und Speicherung
-------------------------------------

.. automodule:: tatooine_data.aquire_data
   :members:
   :private-members: _MAX_DATA_POINTS_HISTORY, 

.. automodule:: tatooine_data.store_data
   :members:
   :private-members: _MEASUREMENT_NAME,_TAG_LOCATION

@dataclass als Speicherformat für die Messdaten
-----------------------------------------------

.. automodule:: tatooine_data.datapoint
   :members:

Allgemeine Helper Funktionen
------------------------------

.. automodule:: tatooine_data.helper
   :members:
