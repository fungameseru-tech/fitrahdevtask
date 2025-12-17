@echo off
echo ============================================
echo   Taskmaster - Vercel Deployment Script
echo ============================================
echo.

cd /d "d:\Semester 8\Taskmaster"

REM Clean previous config
if exist .vercel rmdir /s /q .vercel

echo Deploying to Vercel...
echo.
echo Jawab pertanyaan berikut:
echo 1. Set up and deploy? =^> Y
echo 2. Link to existing project? =^> N
echo 3. Project name? =^> taskmaster-portfolio
echo 4. Directory? =^> ./ (tekan Enter)
echo 5. Override settings? =^> N
echo.

REM Deploy
call vercel --prod

echo.
echo ============================================
echo   Deployment Complete!
echo ============================================
pause
