@echo off
setlocal EnableExtensions DisableDelayedExpansion
REM Hosted-only real Windows packaging canary. Called by existing GitHub Actions
REM workflow under a trusted same-repo PR, never by owner HP.
if not defined UR_NINJA_ROOT exit /b 21
if not defined UR_NINJA_FRAMEWORK exit /b 22
if not defined UR_NINJA_WS exit /b 23
if not defined UR_SDL3_PREBUILT_DIR exit /b 24
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" exit /b 25
for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -property installationPath`) do set "VSROOT=%%I"
if not defined VSROOT exit /b 26
if not exist "%VSROOT%\Common7\Tools\VsDevCmd.bat" exit /b 27
call "%VSROOT%\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >NUL
if errorlevel 1 exit /b 28
where ninja.exe >NUL 2>&1
if errorlevel 1 exit /b 29
set "CLANG=%VSROOT%\VC\Tools\Llvm\x64\bin\clang-cl.exe"
if not exist "%CLANG%" exit /b 30
cmake -S "%UR_NINJA_ROOT%" -B "%UR_NINJA_ROOT%/build" -G "Ninja Multi-Config" -DCMAKE_C_COMPILER="%CLANG%" -DCMAKE_CXX_COMPILER="%CLANG%" -DSNESRECOMP_ROOT="%UR_NINJA_FRAMEWORK%" -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=OFF -DSDL3_DIR="%UR_SDL3_PREBUILT_DIR%" -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded -DSNESRECOMP_SDL3_SOURCE_DIR="%UR_NINJA_WS%/.tools/src/sdl3/SDL3-3.4.10"
if errorlevel 1 exit /b 31
cmake --build "%UR_NINJA_ROOT%/build" --config Release --parallel 6
if errorlevel 1 exit /b 32
echo NINJA_FULL_PACKAGE=compiled
exit /b 0
