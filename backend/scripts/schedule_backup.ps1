# 백업을 주 1회 저절로 돌게 등록 (윈도우 작업 스케줄러)
#
#   1) 접속 문자열을 파일에 한 줄로 적어 둡니다 (깃 저장소 바깥)
#        New-Item -ItemType Directory -Force "$env:USERPROFILE\.relaystory" | Out-Null
#        "postgresql://...neon.tech/neondb?sslmode=require" | Set-Content "$env:USERPROFILE\.relaystory\db-url.txt" -Encoding utf8 -NoNewline
#   2) backend 폴더에서 이 파일을 돌립니다
#        powershell -ExecutionPolicy Bypass -File scripts\schedule_backup.ps1
#
# 지울 때:  powershell -ExecutionPolicy Bypass -File scripts\schedule_backup.ps1 -Remove
#
# 접속 문자열은 작업에 적히지 않습니다 — 작업 스케줄러 화면이나 실행 중인 프로그램 목록에
# 그대로 보이면 안 되므로, 파일 경로만 넘기고 내용은 백업 프로그램이 읽습니다.

param(
    [string]$Name = "옛날 옛적에 - DB 백업",
    [string]$UrlFile = "$env:USERPROFILE\.relaystory\db-url.txt",
    [string]$At = "03:00",
    [string]$DayOfWeek = "Sunday",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$backend = Split-Path -Parent $PSScriptRoot

if ($Remove) {
    Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    "지웠습니다: $Name"
    return
}

if (-not (Test-Path $UrlFile)) {
    "접속 문자열 파일이 없습니다: $UrlFile"
    "Neon 접속 문자열을 붙여넣어 주세요 (화면에 보이지 않습니다)"
    $secret = Read-Host -AsSecureString "접속 문자열"
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret))
    if (-not $plain.StartsWith("postgres")) { throw "postgresql:// 로 시작해야 합니다." }

    New-Item -ItemType Directory -Force (Split-Path -Parent $UrlFile) | Out-Null
    # 맨 앞에 표식(BOM)이 들어가면 pg_dump가 주소를 못 알아봄 → BOM 없는 UTF-8로 씀
    [IO.File]::WriteAllText($UrlFile, $plain, (New-Object Text.UTF8Encoding $false))
    # 이 컴퓨터의 나만 읽을 수 있게
    icacls $UrlFile /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
    "저장했습니다: $UrlFile"
}

$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { throw "uv 를 찾지 못했습니다. PATH에 있는지 확인해 주세요." }

# 창 없이 조용히 돌리기 위해 uv 를 직접 부름 (cmd 창이 뜨지 않음)
$action = New-ScheduledTaskAction -Execute $uv `
    -Argument "run python -m scripts.backup --url-file `"$UrlFile`"" `
    -WorkingDirectory $backend

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $At

# 컴퓨터가 꺼져 있어 지나갔으면 다음에 켰을 때 한 번 돌림 / 배터리로 돌아도 멈추지 않음
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger `
    -Settings $settings -Description "운영 DB를 주 1회 받아 둡니다 (최신 1개만 덮어쓰기)" -Force | Out-Null

"등록했습니다: $Name ($DayOfWeek $At)"
"지금 한 번 돌려 보기:  Start-ScheduledTask -TaskName '$Name'"
"결과 보기:            Get-Content '$backend\backups\last-runs.txt' -Tail 5"
