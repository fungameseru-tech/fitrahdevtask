Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Taskmaster - Vercel Deployment" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "d:\Semester 8\Taskmaster"

# Clean environment
Remove-Item Env:\VERCEL_ORG_ID -ErrorAction SilentlyContinue
Remove-Item Env:\VERCEL_PROJECT_ID -ErrorAction SilentlyContinue

# Clean previous config
if (Test-Path ".vercel") {
    Remove-Item -Recurse -Force ".vercel"
    Write-Host "Cleaned previous config" -ForegroundColor Green
}

Write-Host ""
Write-Host "Deploying to Vercel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Jawab pertanyaan berikut:" -ForegroundColor Cyan
Write-Host "1. Set up and deploy? => Y"
Write-Host "2. Which scope? => Pilih account Anda"
Write-Host "3. Link to existing project? => N"
Write-Host "4. Project name? => taskmaster-portfolio"
Write-Host "5. Directory? => ./ (tekan Enter)"
Write-Host "6. Override settings? => N"
Write-Host ""

# Deploy
vercel --prod

Write-Host ""
Write-Host "Deployment Complete!" -ForegroundColor Green
