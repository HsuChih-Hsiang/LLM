cd "C:\Users\User\Desktop\pgvector"
set "PGROOT=C:\Program Files\PostgreSQL\16"
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
nmake /F Makefile.win
nmake /F Makefile.win install
pause