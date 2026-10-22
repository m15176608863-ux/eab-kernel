@echo off
rem WO-C0: pinned VS2022 Community CMake/Ninja, MSVC 14.44.35207 x64.
rem Pure ASCII. No clean/delete option; build products remain under eab2/build.
setlocal
set "VSDIR=C:\Program Files\Microsoft Visual Studio\2022\Community"
set "CMAKE=%VSDIR%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
set "NINJA=%VSDIR%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
if not exist "%CMAKE%" exit /b 2
if not exist "%NINJA%" exit /b 2
if defined CL exit /b 2
if defined _CL_ exit /b 2
set "PATH=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer;%PATH%"
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" -vcvars_ver=14.44.35207
if errorlevel 1 exit /b %errorlevel%
set "VSLANG=1033"
set "TEMP=%~dp0..\reports\codex\C0_evidence\tmp"
set "TMP=%TEMP%"
if not exist "%TEMP%" mkdir "%TEMP%"
cd /d "%~dp0"
"%CMAKE%" --version
"%NINJA%" --version
where cl
"%CMAKE%" -S . -B build -G Ninja -DCMAKE_MAKE_PROGRAM="%NINJA%" -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 exit /b %errorlevel%
"%CMAKE%" --build build --verbose
if errorlevel 1 exit /b %errorlevel%
"%CMAKE%" -E chdir build "%NINJA%" -t commands
if errorlevel 1 exit /b %errorlevel%
build\eab2_test_numeric.exe
if errorlevel 1 exit /b %errorlevel%
build\eab2_test_abi.exe
if errorlevel 1 exit /b %errorlevel%
build\eab2_test_c_header.exe
if errorlevel 1 exit /b %errorlevel%
build\eab2_test_c_header_static.exe
exit /b %errorlevel%
