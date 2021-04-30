# Pi4-Inventory-System
Uses Object Detection trained with Tensorflow, run through OpenCV via Python that detects a projector coming into contact on a trigger-line, then records whether the item was borrowed or returned depending on the direction the item entered the line.

Uses pyQt5 as GUI on a Pi4B+ Linux OS to output the records, while using SQLite as database.
 
Involves threading so camera feed will not block access to GUI.
