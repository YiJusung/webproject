# 프론트엔드 환경 변수 설정 스크립트

Write-Host "=" * 70
Write-Host "🔧 프론트엔드 환경 변수 설정"
Write-Host "=" * 70
Write-Host ""

# ngrok 터널 확인
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
    $tunnels = ($response.Content | ConvertFrom-Json).tunnels
    
    $backendUrl = $null
    $frontendUrl = $null
    
    foreach ($tunnel in $tunnels) {
        $addr = $tunnel.config.addr
        $publicUrl = $tunnel.public_url
        
        if ($addr -like "*:8000*") {
            $backendUrl = $publicUrl
            Write-Host "✅ 백엔드 터널 발견: $backendUrl"
        } elseif ($addr -like "*:3000*") {
            $frontendUrl = $publicUrl
            Write-Host "✅ 프론트엔드 터널 발견: $frontendUrl"
        }
    }
    
    if (-not $backendUrl) {
        Write-Host ""
        Write-Host "❌ 백엔드 ngrok 터널이 없습니다!"
        Write-Host ""
        Write-Host "다음 단계:"
        Write-Host "1. 새 터미널을 열고 다음 명령어 실행:"
        Write-Host "   ngrok http 8000"
        Write-Host ""
        Write-Host "2. 백엔드 ngrok URL을 복사한 후"
        Write-Host "3. 이 스크립트를 다시 실행하거나"
        Write-Host "4. frontend/.env 파일을 수동으로 수정:"
        Write-Host "   REACT_APP_API_URL=https://[백엔드-ngrok-URL]/api"
        exit 1
    }
    
    # .env 파일 생성/수정
    $envContent = "REACT_APP_API_URL=$backendUrl/api"
    $envPath = "frontend\.env"
    
    Set-Content -Path $envPath -Value $envContent -Force
    
    Write-Host ""
    Write-Host "✅ frontend/.env 파일이 설정되었습니다:"
    Write-Host "   $envContent"
    Write-Host ""
    Write-Host "⚠️  프론트엔드 서버를 재시작해야 합니다!"
    Write-Host "   Ctrl+C로 중지한 후 npm start로 다시 시작하세요."
    
} catch {
    Write-Host "❌ ngrok API에 접근할 수 없습니다."
    Write-Host "   ngrok이 실행 중인지 확인하세요."
    Write-Host ""
    Write-Host "수동 설정 방법:"
    Write-Host "1. 백엔드 ngrok 터널 시작: ngrok http 8000"
    Write-Host "2. frontend/.env 파일 생성:"
    Write-Host "   REACT_APP_API_URL=https://[백엔드-ngrok-URL]/api"
}

