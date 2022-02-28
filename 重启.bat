@echo off
title 重启购物平台

taskkill /f /t /im 购物平台启动程序.exe
timeout 1
cd C:\Users\Administrator\Desktop\ShoppingHelper
start 购物平台启动程序.exe
::exit