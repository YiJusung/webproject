# ngrok 터널 자동 설정 스크립트
# 백엔드와 프론트엔드를 각각 별도 터미널에서 실행

Write-Host "=" * 70
Write-Host "🌐 ngrok 터널 설정 도우미"
Write-Host "=" * 70
Write-Host ""

# 1. 기존 ngrok 프로세스 종료
Write-Host "🧹 기존 ngrok 프로세스 정리 중..."
$ngrokProcesses = Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}
if ($ngrokProcesses) {
    $ngrokProcesses | Stop-Process -Force
    Write-Host "✅ 기존 ngrok 프로세스 종료 완료"
    Start-Sleep -Seconds 2
} else {
    Write-Host "ℹ️  실행 중인 ngrok 프로세스가 없습니다"
}

Write-Host ""
Write-Host "=" * 70
Write-Host "📋 다음 단계를 따라주세요:"
Write-Host "=" * 70
Write-Host ""
Write-Host "1️⃣  새 터미널을 열고 백엔드 ngrok 터널 시작:"
Write-Host "    ngrok http 8000"
Write-Host ""
Write-Host "2️⃣  또 다른 새 터미널을 열고 프론트엔드 ngrok 터널 시작:"
Write-Host "    ngrok http 3000"
Write-Host ""
Write-Host "3️⃣  각 터미널에 표시되는 URL을 복사하세요"
Write-Host ""
Write-Host "4️⃣  프론트엔드 환경 변수 설정:"
Write-Host "    frontend/.env 파일에 다음을 추가:"
Write-Host "    REACT_APP_API_URL=https://[백엔드-ngrok-URL]/api"
Write-Host ""
Write-Host "=" * 70
Write-Host "💡 팁: 각 ngrok 터널은 별도 터미널에서 실행해야 합니다!"
Write-Host "=" * 70

