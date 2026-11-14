API: Package ``tatooine_data`` (Messdatenerfassung)
====================================================

In diesem Package sind alle Module zur Erfassung, Berechnung und Speicherung
der Messdaten des Tatooine Monitor enthalten. Das Benachrichtigungssystem
liegt ebenfalls in diesem Package und ist in :doc:`alerting` dokumentiert.

Zentrale Datenerfassung
-----------------------

.. automodule:: tatooine_data.aquire_data
   :members:

Dataclass als Speicherformat für die Messdaten
-----------------------------------------------

.. automodule:: tatooine_data.datapoint
   :members:

Speicherung in der InfluxDB
---------------------------

.. automodule:: tatooine_data.store_data
   :members:

GPIO-Service
------------

.. automodule:: tatooine_data.gpio_service
   :members:

Allgemeine Helper-Funktionen
----------------------------

.. automodule:: tatooine_data.helper
   :members:
