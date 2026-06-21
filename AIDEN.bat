@echo off
title AIDEN - Asistente
cd /d "c:\Users\Usuario\Desktop\Python Proyecto\SLIDE-AI-BUTLER"
call Asistente_Slide_311\Scripts\activate.bat
python Main_AlwaysOn.py > AIDEN_log.txt 2>&1
