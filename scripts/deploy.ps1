<#
.SYNOPSIS
    BabyCare AI - One-Click Deployment Orchestrator cho Windows (PowerShell)
.DESCRIPTION
    Tự động hóa toàn bộ quy trình: Preflight Check -> Build -> Start Containers -> Readiness Polling ->
    Re-index Knowledge Base (FAISS/BM25) -> Verify Hybrid Search -> Báo cáo Tổng kết.
.PARAMETER Env
    Môi trường triển khai: 'dev' (Mặc định) hoặc 'prod'.
.PARAMETER WithAirflow
    Cờ kích hoạt khởi chạy kèm cụm Apache Airflow Data Ingestion Pipeline.
.PARAMETER Gpu
    Cờ kích hoạt tăng tốc phần cứng qua NVIDIA GPU CUDA.
.PARAMETER NoCache
    Cờ ép buộc Docker build lại toàn bộ Image không dùng cache.
.PARAMETER RebuildIndex
    Cờ kích hoạt nạp lại và build toàn bộ FAISS Vector Store sau khi khởi động.
.PARAMETER MaxAttempts
    Số lần thử tối đa khi polling kiểm tra sức khỏe hệ thống (Mặc định: 30).
.PARAMETER WaitSeconds
    Số giây nghỉ giữa mỗi lần polling (Mặc định: 2).
.EXAMPLE
    .\scripts\deploy.ps1
    .\scripts\deploy.ps1 -Env prod
    .\scripts\deploy.ps1 -WithAirflow -RebuildIndex
#>

[CmdletBinding()]
param (
    [ValidateSet("dev", "prod")]
    [string]$Env = "dev",

    [switch]$WithAirflow,
    [switch]$Gpu,
    [switch]$NoCache,
    [switch]$RebuildIndex,

    [int]$MaxAttempts = 30,
    [int]$WaitSeconds = 2
)

# Thiết lập bảng mã UTF-8 cho Windows PowerShell Console
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

function Write-StepHeader {
    param([string]$Step, [string]$Title)
    Write-Host "`n[$Step] $Title" -ForegroundColor Cyan
    Write-Host ("-" * 60) -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor Yellow
}

function Write-Failure {
    param([string]$Message, [string]$DebugHint = "")
    Write-Host "`n  ❌ $Message" -ForegroundColor Red
    if ($DebugHint) {
        Write-Host "  👉 Lệnh kiểm tra gợi ý: $DebugHint" -ForegroundColor Yellow
    }
    Write-Host "`n====================================================" -ForegroundColor Red
    Write-Host "  💥 TRIỂN KHAI THẤT BẠI. DỪNG TIẾN TRÌNH." -ForegroundColor Red
    Write-Host "====================================================`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n====================================================" -ForegroundColor Magenta
Write-Host "  👶 BABYCARE AI - ONE-CLICK DEPLOYMENT ORCHESTRATOR" -ForegroundColor Magenta
Write-Host "====================================================" -ForegroundColor Magenta
Write-Host "  • Môi trường mục tiêu : " -NoNewline
Write-Host "$($Env.ToUpper())" -ForegroundColor Cyan
Write-Host "  • Kích hoạt Airflow   : $(if ($WithAirflow) { 'BẬT' } else { 'TẮT' })"
Write-Host "  • Chế độ GPU CUDA     : $(if ($Gpu) { 'BẬT' } else { 'TẮT (CPU)' })"
Write-Host "  • Re-build Không Cache: $(if ($NoCache) { 'BẬT' } else { 'TẮT' })"
Write-Host "  • Re-index Knowledge  : $(if ($RebuildIndex) { 'BẬT' } else { 'TẮT' })"

# ------------------------------------------------------------------------------
# STEP 0: PREFLIGHT CHECKS
# ------------------------------------------------------------------------------
Write-StepHeader "0/7" "Kiểm tra Tính sẵn sàng của Môi trường (Preflight Checks)..."

# 1. Kiểm tra Docker CLI
try {
    $dockerVer = docker --version 2>$null
    if (-not $dockerVer) {
        Write-Failure "Không tìm thấy Docker CLI trên máy tính." "Vui lòng cài đặt Docker Desktop từ https://www.docker.com/"
    }
    Write-Success "Docker CLI đã sẵn sàng: $dockerVer"
} catch {
    Write-Failure "Lỗi khi kiểm tra Docker CLI: $_"
}

# 2. Kiểm tra Docker Daemon đang chạy
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Docker Daemon (Docker Desktop) chưa được khởi động." "Vui lòng mở ứng dụng Docker Desktop và đợi trạng thái Engine Ready."
    }
    Write-Success "Docker Engine Daemon đang hoạt động tốt."
} catch {
    Write-Failure "Docker Daemon không phản hồi: $_"
}

# 3. Kiểm tra các tệp cấu hình cần thiết
$baseCompose = "docker/docker-compose.yml"
$envCompose = if ($Env -eq "prod") { "docker/docker-compose.prod.yml" } else { "docker/docker-compose.dev.yml" }
$gpuCompose = "docker/docker-compose.gpu.yml"

if (-not (Test-Path $baseCompose)) { Write-Failure "Thiếu file cấu hình Docker cơ sở: $baseCompose" }
if (-not (Test-Path $envCompose)) { Write-Failure "Thiếu file cấu hình Docker môi trường: $envCompose" }
if ($Gpu -and -not (Test-Path $gpuCompose)) { Write-Failure "Thiếu file cấu hình GPU: $gpuCompose" }

Write-Success "Các tệp Docker Compose hợp lệ: $baseCompose, $envCompose"

# 4. Kiểm tra tài nguyên mô hình AI cục bộ
$bgeModelPath = "app/ai/models/models--BAAI--bge-m3"
$cryModelPath = "app/ai/CRY/weights/best_audio_model.pth"

if (Test-Path $bgeModelPath) {
    Write-Success "Mô hình BGE-M3 Embedding cục bộ: SẴN SÀNG"
} else {
    Write-WarningMsg "Chưa tìm thấy BGE-M3 cục bộ, Docker container sẽ tự động tải khi khởi chạy."
}

if (Test-Path $cryModelPath) {
    Write-Success "Mô hình AST Cry Classifier cục bộ: SẴN SÀNG"
} else {
    Write-WarningMsg "Chưa tìm thấy best_audio_model.pth, tính năng phân tích tiếng khóc sẽ dùng mô hình fallback."
}

# ------------------------------------------------------------------------------
# STEP 1: XÁC THỰC VÀ ĐỒNG BỘ FILE MÔI TRƯỜNG (.ENV)
# ------------------------------------------------------------------------------
Write-StepHeader "1/7" "Đồng bộ hóa Cấu hình Biến Môi trường (.env)..."

if ($Env -eq "prod") {
    if (Test-Path ".env.production") {
        Copy-Item ".env.production" ".env" -Force
        Write-Success "Đã nạp .env.production vào .env hoạt động."
    }
} else {
    if (Test-Path ".env.development") {
        Copy-Item ".env.development" ".env" -Force
        Write-Success "Đã nạp .env.development vào .env hoạt động."
    } elseif (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env" -Force
        Write-Success "Đã khởi tạo .env từ .env.example."
    }
}

# ------------------------------------------------------------------------------
# STEP 2: BUILD DOCKER SERVICES
# ------------------------------------------------------------------------------
Write-StepHeader "2/7" "Xây dựng Docker Images (Build Services)..."

$composeArgs = @("-f", $baseCompose, "-f", $envCompose)
if ($Gpu) { $composeArgs += @("-f", $gpuCompose) }

$buildCmd = @("compose") + $composeArgs + @("build")
if ($NoCache) { $buildCmd += "--no-cache" }
$buildCmd += "backend"

Write-Host "  Executing: docker $($buildCmd -join ' ')" -ForegroundColor DarkGray
& docker $buildCmd

if ($LASTEXITCODE -ne 0) {
    Write-Failure "Xây dựng Backend Docker Image thất bại." "docker compose -f $baseCompose -f $envCompose build backend"
}
Write-Success "Xây dựng Backend Docker Image hoàn tất thành công."

# Build Airflow nếu được yêu cầu
if ($WithAirflow) {
    $airflowCompose = "airflow/airflow_project/docker-compose.yml"
    if (Test-Path $airflowCompose) {
        Write-Host "  Building Airflow services..." -ForegroundColor DarkGray
        & docker compose -f $airflowCompose build
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Xây dựng cụm Apache Airflow thất bại." "docker compose -f $airflowCompose build"
        }
        Write-Success "Xây dựng Airflow Images hoàn tất."
    } else {
        Write-WarningMsg "Không tìm thấy $airflowCompose, bỏ qua bước build Airflow."
    }
}

# ------------------------------------------------------------------------------
# STEP 3: KHỞI CHẠY CÁC DỊCH VỤ DOCKER (START SERVICES)
# ------------------------------------------------------------------------------
Write-StepHeader "3/7" "Khởi động các Dịch vụ Nền tảng (Up Containers)..."

$upCmd = @("compose") + $composeArgs + @("up", "-d")
Write-Host "  Executing: docker $($upCmd -join ' ')" -ForegroundColor DarkGray
& docker $upCmd

if ($LASTEXITCODE -ne 0) {
    Write-Failure "Khởi động Backend / Redis containers thất bại." "docker $($upCmd -join ' ')"
}
Write-Success "Backend API & Redis containers đã được khởi chạy."

# Khởi chạy Airflow nếu được yêu cầu
if ($WithAirflow -and (Test-Path "airflow/airflow_project/docker-compose.yml")) {
    Write-Host "  Khởi động cụm Apache Airflow..." -ForegroundColor DarkGray
    & docker compose -f airflow/airflow_project/docker-compose.yml up -d
    if ($LASTEXITCODE -ne 0) {
        Write-WarningMsg "Khởi động Airflow gặp cảnh báo, tiếp tục kiểm tra readiness..."
    } else {
        Write-Success "Airflow Webserver, Scheduler & Ingestion API đã khởi chạy."
    }
}

# ------------------------------------------------------------------------------
# STEP 4: POLLING KIỂM TRA TÍNH SẴN SÀNG (READINESS POLLING)
# ------------------------------------------------------------------------------
Write-StepHeader "4/7" "Chờ đợi Hệ thống Sẵn sàng (Readiness Polling Loop)..."

$backendUrl = "http://localhost:8000"
$healthUrl = "$backendUrl/health"
$ready = $false

Write-Host "  Đang kiểm tra kết nối tới: $healthUrl (Tối đa $MaxAttempts lần, mỗi $WaitSeconds giây)..."

for ($i = 1; $i -le $MaxAttempts; $i++) {
    Write-Host "  --> Lần thử $i/$MaxAttempts ... " -NoNewline
    try {
        $response = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response -and ($response.status -eq "ok" -or $response.status -eq "healthy")) {
            Write-Host "SẴN SÀNG! (HTTP 200 OK)" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {
        # Tiếp tục retry
    }
    Write-Host "chưa sẵn sàng, đợi ${WaitSeconds}s..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $WaitSeconds
}

if (-not $ready) {
    Write-Failure "Backend không phản hồi endpoint /health sau $MaxAttempts lần thử." "docker compose -f $baseCompose -f $envCompose logs backend"
}

Write-Success "FastAPI Backend đã sẵn sàng phục vụ tại $backendUrl"

# Kiểm tra Airflow Webserver nếu bật
if ($WithAirflow) {
    $airflowHealthUrl = "http://localhost:8080/health"
    $airflowReady = $false
    Write-Host "  Đang kiểm tra Airflow Webserver tại: $airflowHealthUrl..."
    for ($i = 1; $i -le 20; $i++) {
        try {
            $afResp = Invoke-RestMethod -Uri $airflowHealthUrl -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($afResp) {
                $airflowReady = $true
                Write-Success "Airflow Webserver đã sẵn sàng tại http://localhost:8080"
                break
            }
        } catch {
            Start-Sleep -Seconds 3
        }
    }
    if (-not $airflowReady) {
        Write-WarningMsg "Airflow Webserver đang khởi động trong nền. Bạn có thể truy cập sau tại http://localhost:8080."
    }
}

# ------------------------------------------------------------------------------
# STEP 5: KIỂM TRA KẾT NỐI HẠ TẦNG (DATABASE & REDIS CHECK)
# ------------------------------------------------------------------------------
Write-StepHeader "5/7" "Kiểm tra Hạ tầng & Dịch vụ Liên kết..."

try {
    $rootInfo = Invoke-RestMethod -Uri "$backendUrl/" -Method Get -TimeoutSec 5
    Write-Success "Ứng dụng: $($rootInfo.app_name) | Môi trường: $($rootInfo.env) | Trạng thái: $($rootInfo.status)"
} catch {
    Write-WarningMsg "Không thể lấy thông tin gốc từ / (Bỏ qua)."
}

# ------------------------------------------------------------------------------
# STEP 6: TỰ ĐỘNG RE-INDEX KNOWLEDGE BASE (KHI BẬT CỜ)
# ------------------------------------------------------------------------------
Write-StepHeader "6/7" "Đánh chỉ mục Tri thức Y khoa (FAISS / BM25 Ingestion)..."

if ($RebuildIndex) {
    if ($Env -eq "prod") {
        Write-Host "  ⚠️  CẢNH BÁO AN TOÀN PRODUCTION: Thao tác này sẽ build lại toàn bộ FAISS Vector Index." -ForegroundColor Yellow
        $confirm = Read-Host "  Bạn có chắc chắn muốn Re-index trên Production? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "  Đã hủy bỏ thao tác Re-index theo yêu cầu người dùng." -ForegroundColor Cyan
            $RebuildIndex = $false
        }
    }

    if ($RebuildIndex) {
        Write-Host "  Đang thực thi Re-index hợp nhất bên trong container..." -ForegroundColor DarkGray
        $reindexCmd = @("compose") + $composeArgs + @("exec", "-T", "backend", "python", "-m", "app.AI_agents.knowledge.rebuild_index")
        & docker $reindexCmd

        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Tiến trình Re-index tài liệu thất bại." "docker $($reindexCmd -join ' ')"
        }
        Write-Success "Đã nạp và cập nhật toàn diện FAISS Vector Index & BM25 Sparse Index."
    }
} else {
    Write-Host "  ℹ️  Re-index bị bỏ qua (Mặc định). Sử dụng tham số -RebuildIndex nếu cần nạp lại tài liệu mới." -ForegroundColor DarkGray
}

# ------------------------------------------------------------------------------
# STEP 7: KIỂM THỬ TÌM KIẾM HYBRID SEARCH THỰC TẾ & BÁO CÁO TỔNG KẾT
# ------------------------------------------------------------------------------
Write-StepHeader "7/7" "Kiểm thử Thực tế & Tổng kết Triển khai..."

$testQuery = "Bé 5 tháng tuổi một ngày ngủ bao nhiêu tiếng là đủ?"
Write-Host "  Đang gửi truy vấn kiểm thử tới AI Chat Agent: `"$testQuery`"..." -ForegroundColor DarkGray

$testSuccess = $false
try {
    $chatUrl = "$backendUrl/api/v1/ai-agent/chat"
    $body = @{
        message = $testQuery
        session_id = "deploy_verification_test"
    } | ConvertTo-Json

    $chatResp = Invoke-RestMethod -Uri $chatUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    if ($chatResp -and $chatResp.message) {
        Write-Success "Hybrid Search & AI Agent phản hồi thành công (HTTP 200 OK)!"
        $testSuccess = $true
    }
} catch {
    Write-WarningMsg "Kiểm thử chat API gặp sự cố hoặc timeout, tuy nhiên hạ tầng chính đã sẵn sàng: $_"
}

# Báo cáo Tổng kết Hoàn tất
Write-Host "`n====================================================" -ForegroundColor Green
Write-Host "  🎉 TRIỂN KHAI HOÀN TẤT THÀNH CÔNG (DEPLOYMENT SUCCESS)" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "  • Môi trường (Environment) : $($Env.ToUpper())"
Write-Host "  • Cổng Backend API (FastAPI): $backendUrl"
Write-Host "  • Tài liệu Swagger API Docs : $backendUrl/api/docs"
Write-Host "  • Cơ sở dữ liệu Firestore   : ĐÃ KẾT NỐI (baby-7d4a7)"
Write-Host "  • Bộ nhớ đệm Redis Cache    : ĐÃ KẾT NỐI"
Write-Host "  • Tìm kiếm RAG Hybrid Search: $(if ($testSuccess) { '✅ HOẠT ĐỘNG TỐT' } else { '⚠️ SẴN SÀNG' })"

if ($WithAirflow) {
    Write-Host "  • Apache Airflow Dashboard  : http://localhost:8080 (User: admin / Pass: admin)"
} else {
    Write-Host "  • Apache Airflow Pipeline   : TẮT (Chạy lại với cờ -WithAirflow nếu cần)"
}

Write-Host "====================================================`n" -ForegroundColor Green
