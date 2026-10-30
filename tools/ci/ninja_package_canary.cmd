@echo off
setlocal EnableExtensions DisableDelayedExpansion
REM Private helper invoked only after canonical workflow guards, not by untrusted PR.
if not defined UR_NINJA_ROOT exit /b 21
if not defined UR_NINJA_FRAMEWORK exit /b 22
if not defined UR_NINJA_WS exit /b 23
if not defined UR_SDL3_PREBUILT_DIR exit /b 24
if /I "%UR_HP_NINJA_CANARY%"=="1" (
  if not defined UR_HP_NINJA_DIR exit /b 33
  if not exist "%UR_HP_NINJA_DIR%\ninja.exe" exit /b 34
)
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" exit /b 25
for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -property installationPath`) do set "VSROOT=%%I"
if not defined VSROOT exit /b 26
if not exist "%VSROOT%\Common7\Tools\VsDevCmd.bat" exit /b 27
call "%VSROOT%\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >NUL
if errorlevel 1 exit /b 28
REM Prepend verified owner Ninja *after* VS DevCmd sets its own PATH.
REM Bind CMake to the exact receipt-hashed executable: PATH/where alone
REM do not ensure selection identity on Windows.
set "OWNER_NINJA_ARG="
if /I "%UR_HP_NINJA_CANARY%"=="1" (
  set "PATH=%UR_HP_NINJA_DIR%;%PATH%"
  set "OWNER_NINJA_ARG=-DCMAKE_MAKE_PROGRAM=%UR_HP_NINJA_DIR%/ninja.exe"
)
where ninja.exe
if errorlevel 1 exit /b 29
set "CLANG=%VSROOT%\VC\Tools\Llvm\x64\bin\clang-cl.exe"
if not exist "%CLANG%" exit /b 30
cmake -S "%UR_NINJA_ROOT%" -B "%UR_NINJA_ROOT%/build" -G "Ninja Multi-Config" -DCMAKE_C_COMPILER="%CLANG%" -DCMAKE_CXX_COMPILER="%CLANG%" -DSNESRECOMP_ROOT="%UR_NINJA_FRAMEWORK%" -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=OFF -DSDL3_DIR="%UR_SDL3_PREBUILT_DIR%" -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded -DSNESRECOMP_SDL3_SOURCE_DIR="%UR_NINJA_WS%/.tools/src/sdl3/SDL3-3.4.10" %OWNER_NINJA_ARG%
if errorlevel 1 exit /b 31
cmake --build "%UR_NINJA_ROOT%/build" --config Release --parallel 6
if errorlevel 1 exit /b 32
echo HP_NINJA_CANARY=actual_game_compiled
exit /b 0
