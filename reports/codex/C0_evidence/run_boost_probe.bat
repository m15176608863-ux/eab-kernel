@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" -vcvars_ver=14.44.35207
if errorlevel 1 exit /b %errorlevel%
set "TEMP=%~dp0tmp"
set "TMP=%~dp0tmp"
cd /d "%~dp0tmp"
where cl
cl /nologo /std:c++20 /O2 /utf-8 /permissive- /fp:precise /MD /EHsc /showIncludes /I"%~dp0tmp\boost_probe_include" "%~dp0boost_probe.cpp" /Fo"%~dp0tmp\boost_probe.obj" /Fe"%~dp0tmp\boost_probe.exe"
if errorlevel 1 exit /b %errorlevel%
"%~dp0tmp\boost_probe.exe"
exit /b %errorlevel%
