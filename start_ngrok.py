"""
ngrok 터널링 서버 시작 스크립트
인터넷 어디서나 접속 가능하도록 ngrok 터널을 생성합니다.
"""
import subprocess
import sys
import time
import re
import requests
import platform
from pathlib import Path

def stop_existing_ngrok_tunnels():
    """
    실행 중인 ngrok 프로세스와 터널을 종료합니다.
    """
    try:
        # ngrok API를 통해 실행 중인 터널 확인
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                if tunnels:
                    print(f"⚠️  실행 중인 ngrok 터널 {len(tunnels)}개 발견. 종료 중...")
        except:
            pass  # ngrok API에 접근할 수 없으면 무시
        
        # Windows에서 ngrok 프로세스 종료
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq ngrok.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "ngrok.exe" in result.stdout:
                    print("🛑 실행 중인 ngrok 프로세스 종료 중...")
                    subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                                 capture_output=True, timeout=5)
                    time.sleep(2)  # 프로세스 종료 대기
            except:
                pass
        else:
            # Linux/Mac에서 ngrok 프로세스 종료
            try:
                subprocess.run(["pkill", "-f", "ngrok"], 
                             capture_output=True, timeout=5)
                time.sleep(2)
            except:
                pass
    except Exception as e:
        print(f"⚠️  기존 ngrok 프로세스 종료 중 오류 (무시하고 계속): {e}")

def get_ngrok_url(port: int, timeout: int = 10, max_retries: int = 10) -> str:
    """
    ngrok 터널의 공개 URL을 가져옵니다.
    
    Args:
        port: 터널링할 로컬 포트
        timeout: 타임아웃 (초)
        max_retries: 최대 재시도 횟수
    
    Returns:
        ngrok 공개 URL (예: https://abc123.ngrok.io)
    """
    for attempt in range(max_retries):
        try:
            # ngrok API를 통해 터널 정보 가져오기
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                for tunnel in tunnels:
                    addr = tunnel.get("config", {}).get("addr", "")
                    # localhost:포트 또는 127.0.0.1:포트 형식 모두 확인
                    if f":{port}" in addr and ("localhost" in addr or "127.0.0.1" in addr):
                        url = tunnel.get("public_url", "")
                        if url:
                            return url
            # 터널이 아직 준비되지 않았으면 잠시 대기 후 재시도
            if attempt < max_retries - 1:
                time.sleep(1)
        except requests.exceptions.ConnectionError:
            # API가 아직 준비되지 않았으면 재시도
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"⚠️ ngrok API에 연결할 수 없습니다 (포트 4040)")
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️ ngrok API 조회 실패: {e}")
    return ""

def start_ngrok_tunnel(port: int, name: str, retry_count: int = 0):
    """
    ngrok 터널을 시작합니다.
    
    Args:
        port: 터널링할 로컬 포트
        name: 터널 이름 (로그용)
    """
    print(f"\n{'='*70}")
    print(f"🌐 {name} ngrok 터널 시작 중...")
    print(f"{'='*70}\n")
    
    try:
        # ngrok 프로세스 시작 (고유한 이름 지정으로 충돌 방지)
        tunnel_name = f"trendpulse_{name.lower()}_{port}"
        process = subprocess.Popen(
            ["ngrok", "http", str(port), "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 잠시 대기 (ngrok이 시작될 시간)
        time.sleep(3)
        
        # 프로세스 상태 확인 (non-blocking)
        process_status = process.poll()
        
        if process_status is not None:
            # 프로세스가 종료된 경우 (오류 발생)
            stdout, stderr = process.communicate()
            error_output = stderr or stdout
            
            # 인증 오류 확인
            if "authentication" in error_output.lower() or "authtoken" in error_output.lower():
                print(f"❌ {name} ngrok 인증 실패!")
                print(f"   오류 메시지:")
                for line in error_output.split('\n'):
                    if line.strip() and ('ERROR' in line or 'authentication' in line.lower() or 'authtoken' in line.lower()):
                        print(f"   {line}")
                print(f"\n📋 해결 방법:")
                print(f"   1. https://dashboard.ngrok.com/get-started/your-authtoken 접속")
                print(f"   2. 올바른 인증 토큰 복사 (형식: 2abc...로 시작)")
                print(f"   3. 다음 명령어 실행: ngrok config add-authtoken YOUR_AUTH_TOKEN")
                return None, None
            # "already online" 오류 확인
            elif "already online" in error_output.lower() or "already in use" in error_output.lower():
                if retry_count < 2:  # 최대 2번 재시도
                    print(f"⚠️  {name} 엔드포인트가 이미 사용 중입니다.")
                    print(f"   기존 터널을 정리하고 재시도합니다... (시도 {retry_count + 1}/2)")
                    stop_existing_ngrok_tunnels()
                    time.sleep(2)
                    # 재시도
                    return start_ngrok_tunnel(port, name, retry_count + 1)
                else:
                    print(f"❌ {name} 터널 시작 실패: 엔드포인트가 계속 사용 중입니다.")
                    print(f"   수동으로 기존 ngrok 프로세스를 종료한 후 다시 시도하세요.")
                    return None, None
            else:
                print(f"❌ {name} ngrok 터널 시작 실패!")
                print(f"   오류: {error_output[:300]}")
                return None, None
        
        # ngrok URL 가져오기 (최대 10초 대기, 1초 간격으로 재시도)
        print(f"⏳ ngrok API 준비 대기 중...")
        url = get_ngrok_url(port, timeout=2, max_retries=10)
        
        if url:
            print(f"✅ {name} ngrok 터널 생성 완료!")
            print(f"📱 공개 URL: {url}")
            print(f"🔗 로컬 포트: {port}")
            print(f"\n💡 다른 기기에서 접속: {url}")
            return url, process
        else:
            # 프로세스가 여전히 실행 중인지 확인
            if process.poll() is None:
                print(f"⚠️ {name} ngrok 프로세스는 실행 중이지만 URL을 가져올 수 없습니다.")
                print(f"   잠시 후 수동으로 확인: http://127.0.0.1:4040 접속")
                print(f"   또는 ngrok 웹 인터페이스에서 URL 확인: http://127.0.0.1:4040")
                # 프로세스는 실행 중이므로 반환 (사용자가 수동으로 확인 가능)
                return None, process
            else:
                # 프로세스가 종료된 경우
                stdout, stderr = process.communicate()
                error_output = stderr or stdout
                if error_output:
                    print(f"❌ {name} ngrok 프로세스가 종료되었습니다.")
                    print(f"   오류 출력: {error_output[:300]}")
                return None, None
            
    except FileNotFoundError:
        print(f"❌ ngrok을 찾을 수 없습니다.")
        print(f"   설치 방법: https://ngrok.com/download")
        print(f"   또는: choco install ngrok")
        return None, None
    except Exception as e:
        print(f"❌ {name} ngrok 터널 시작 실패: {e}")
        return None, None

if __name__ == "__main__":
    print("="*70)
    print("🌐 TrendPulse 인터넷 접속 설정")
    print("="*70)
    print("\n이 스크립트는 ngrok을 사용하여 인터넷 어디서나 접속 가능한")
    print("터널을 생성합니다.\n")
    
    # ngrok 설치 확인
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise FileNotFoundError
        print("✅ ngrok이 설치되어 있습니다.")
    except FileNotFoundError:
        print("❌ ngrok이 설치되어 있지 않습니다.")
        print("\n설치 방법:")
        print("1. https://ngrok.com/download 에서 다운로드")
        print("2. 또는 Chocolatey: choco install ngrok")
        print("3. ngrok 계정 생성 후 인증 토큰 설정:")
        print("   ngrok config add-authtoken YOUR_AUTH_TOKEN")
        sys.exit(1)
    
    # ngrok authtoken 확인
    print("\n🔐 ngrok 인증 토큰 확인 중...")
    try:
        # ngrok config check로 authtoken 확인 시도
        result = subprocess.run(
            ["ngrok", "config", "check"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # authtoken이 설정되어 있으면 정상적으로 실행됨
        if "authtoken" in result.stdout.lower() or "authtoken" in result.stderr.lower():
            print("✅ ngrok 인증 토큰이 설정되어 있습니다.")
        else:
            # authtoken이 없거나 잘못된 경우
            if "authentication" in result.stderr.lower() or "authtoken" in result.stderr.lower():
                print("❌ ngrok 인증 토큰이 올바르지 않거나 설정되지 않았습니다.")
                print("\n📋 인증 토큰 설정 방법:")
                print("1. https://dashboard.ngrok.com/get-started/your-authtoken 접속")
                print("2. 대시보드에서 인증 토큰 복사")
                print("3. 다음 명령어 실행:")
                print("   ngrok config add-authtoken YOUR_AUTH_TOKEN")
                print("\n⚠️  인증 토큰을 설정한 후 다시 이 스크립트를 실행하세요.")
                sys.exit(1)
    except Exception as e:
        # authtoken 확인 실패 시에도 계속 진행 (이미 설정되어 있을 수 있음)
        print("⚠️  ngrok 인증 토큰 확인 중 오류 발생 (계속 진행합니다):", str(e)[:100])
    
    # 기존 ngrok 프로세스 정리
    print("\n🧹 기존 ngrok 프로세스 확인 중...")
    stop_existing_ngrok_tunnels()
    
    # 백엔드 터널 시작
    backend_url, backend_process = start_ngrok_tunnel(8000, "백엔드")
    
    # 프론트엔드 터널 시작
    frontend_url, frontend_process = start_ngrok_tunnel(3000, "프론트엔드")
    
    if backend_url and frontend_url:
        print("\n" + "="*70)
        print("✅ 모든 터널이 준비되었습니다!")
        print("="*70)
        print(f"\n📱 프론트엔드 접속 URL: {frontend_url}")
        print(f"🔌 백엔드 API URL: {backend_url}/api")
        print(f"\n💡 프론트엔드 환경 변수 설정:")
        print(f"   frontend/.env 파일에 다음을 추가:")
        print(f"   REACT_APP_API_URL={backend_url}/api")
        print("\n⚠️  이 창을 닫지 마세요. 터널이 유지됩니다.")
        print("="*70)
        
        try:
            # 프로세스가 종료될 때까지 대기
            if backend_process:
                backend_process.wait()
            if frontend_process:
                frontend_process.wait()
        except KeyboardInterrupt:
            print("\n\n터널을 종료합니다...")
            if backend_process:
                backend_process.terminate()
            if frontend_process:
                frontend_process.terminate()
    else:
        print("\n⚠️  일부 터널 생성에 실패했습니다.")
        print("   ngrok이 실행 중인지, 포트가 사용 중이 아닌지 확인하세요.")

