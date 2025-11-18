@echo off
for /R %%i in (*.xml) do (
xml fo -t "%%i" > test.xml
del "%%i"
move test.xml "%%i"
)