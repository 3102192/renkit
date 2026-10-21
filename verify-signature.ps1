# verify-signature.ps1 — 验证 renkit 发布包签名（Windows PowerShell，纯 .NET 无依赖）
# 用法：将本脚本与 renkit.zip、renkit.zip.sig、LoadForge-公钥.cer 放在同一目录，
#       运行：  powershell -ExecutionPolicy Bypass -File verify-signature.ps1
# 通过输出：  SIGNATURE OK — 包未被篡改
# 失败输出：  SIGNATURE INVALID — 包被修改或签名不匹配

$ErrorActionPreference = "Stop"

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$zipPath   = Join-Path $dir "renkit.zip"
$sigPath   = Join-Path $dir "renkit.zip.sig"
$certPath  = Join-Path $dir "LoadForge-公钥.cer"

foreach ($p in @($zipPath, $sigPath, $certPath)) {
    if (-not (Test-Path $p)) { Write-Host "缺少文件: $p" -ForegroundColor Red; exit 1 }
}

try {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
    $rsa  = [System.Security.Cryptography.RSA]$cert.PublicKey.Key
    $data = [System.IO.File]::ReadAllBytes($zipPath)
    $sig  = [Convert]::FromBase64String((Get-Content $sigPath -Raw).Trim())
    $ok   = $rsa.VerifyData($data, $sig, [System.Security.Cryptography.HashAlgorithmName]::SHA256,
                            [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)
    if ($ok) {
        Write-Host "SIGNATURE OK — 包未被篡改（LoadForge Deploy Center）" -ForegroundColor Green
    } else {
        Write-Host "SIGNATURE INVALID — 包被修改或签名不匹配" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "验证失败: $_" -ForegroundColor Red
    exit 1
}
