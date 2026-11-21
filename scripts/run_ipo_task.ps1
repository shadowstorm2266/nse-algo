<#
Launch wrapper for the IPO recorder's Task Scheduler task (nse-algo-record-ipo-live).

    powershell.exe -NoProfile -NonInteractive -File <repo>\scripts\run_ipo_task.ps1 COMMAND [ARGS...]

Runs COMMAND ARGS from the repo root (the folder above this script) and waits for it,
with PYTHONIOENCODING=utf-8.
stdout and stderr go to data\live\last_launch_stdout.txt and last_launch_stderr.txt
(overwritten each run, outside the backed-up folder). If COMMAND cannot be started, or
exits non-zero, one JSON line is appended to data\live\ipo\launch_failures.jsonl:

    {"time": IST ISO time, "exit_code": int or null, "command": [...],
     "stderr": last 4000 characters of stderr, "start_error": why it could not start or null}

This catches what the recorder's own run_log.jsonl cannot: uv or python failing before
record_ipo_live.py starts (e.g. Windows Smart App Control blocking the interpreter, exit
code 2 from uv, 5 Nov 2026). The file is append-only. ipo_live_backup.py backs it up with
the rest of data\live\ipo; because that backup needs a working Python, the wrapper also
commits this one file to the backup repo and pushes it after each failure (best effort,
git with explicit --git-dir/--work-tree, never the main repo; skipped when the environment
variable NSEALGO_LAUNCH_NO_PUSH is set). The wrapper exits with COMMAND's exit code (1 if
it could not start), so Task Scheduler's "Last Run Result" still shows it.

The environment variable NSEALGO_LAUNCH_ROOT replaces the repo root (tests only).
#>
$ErrorActionPreference = 'Stop'
if ($args.Count -lt 1) { [Console]::Error.WriteLine('usage: run_ipo_task.ps1 COMMAND [ARGS...]'); exit 64 }
$command = [string]$args[0]
$cmdArgs = @($args | Select-Object -Skip 1 | ForEach-Object { [string]$_ })

$repo = if ($env:NSEALGO_LAUNCH_ROOT) { $env:NSEALGO_LAUNCH_ROOT } else { Split-Path -Parent $PSScriptRoot }
$live = Join-Path $repo 'data\live'
$ipo = Join-Path $live 'ipo'
$outFile = Join-Path $live 'last_launch_stdout.txt'
$errFile = Join-Path $live 'last_launch_stderr.txt'
$failLog = Join-Path $ipo 'launch_failures.jsonl'
$utf8 = New-Object System.Text.UTF8Encoding $false

function Get-IstNow {
    (Get-Date).ToUniversalTime().AddHours(5.5).ToString('yyyy-MM-ddTHH:mm:ss.fff') + '+05:30'
}

function Format-Arg([string]$a) {
    if ($a -eq '') { return '""' }
    if ($a -match '[\s"]') { return '"' + ($a -replace '"', '\"') + '"' }
    return $a
}

function Push-FailureLog {
    # Commit launch_failures.jsonl alone to the backup repo and push it. Best effort.
    if ($env:NSEALGO_LAUNCH_NO_PUSH) { return }
    try {
        $cfg = Join-Path $repo 'config\ipo_live.yaml'
        $m = Select-String -Path $cfg -Pattern "^\s*git_dir:\s*'([^']+)'" | Select-Object -First 1
        if (-not $m) { return }
        $gitDir = $m.Matches[0].Groups[1].Value
        if (-not (Test-Path (Join-Path $gitDir 'HEAD'))) { return }
        $env:GIT_TERMINAL_PROMPT = '0'
        $env:GCM_INTERACTIVE = 'never'
        $base = @('-c', 'core.autocrlf=false', "--git-dir=$gitDir", "--work-tree=$ipo")
        Push-Location $gitDir
        try {
            & git @base add -- launch_failures.jsonl 2>$null | Out-Null
            & git @base commit -q -m 'launch failure (run_ipo_task.ps1)' --only -- launch_failures.jsonl 2>$null | Out-Null
            & git @base push -q origin 'HEAD:refs/heads/main' 2>$null | Out-Null
        } finally { Pop-Location }
    } catch { }
}

New-Item -ItemType Directory -Force -Path $ipo | Out-Null
# Redirected, Python's stdio would use the ANSI code page and fail on characters outside
# it (a console never did); UTF-8 keeps prints working and the captured stderr readable.
$env:PYTHONIOENCODING = 'utf-8'
$exitCode = $null
$startError = $null
try {
    $argLine = ($cmdArgs | ForEach-Object { Format-Arg $_ }) -join ' '
    $spArgs = @{ FilePath = $command; WorkingDirectory = $repo; NoNewWindow = $true; Wait = $true;
                 PassThru = $true; RedirectStandardOutput = $outFile; RedirectStandardError = $errFile }
    if ($argLine) { $spArgs['ArgumentList'] = $argLine }
    $proc = Start-Process @spArgs
    $exitCode = [int]$proc.ExitCode
} catch {
    $startError = $_.Exception.Message
}

if ($exitCode -ne 0) {
    $stderr = ''
    if (Test-Path $errFile) { $stderr = [System.IO.File]::ReadAllText($errFile, $utf8) }
    if ($stderr.Length -gt 4000) { $stderr = $stderr.Substring($stderr.Length - 4000) }
    $entry = [ordered]@{
        time = Get-IstNow; exit_code = $exitCode; command = @($command) + $cmdArgs
        stderr = $stderr; start_error = $startError
    }
    $line = ($entry | ConvertTo-Json -Compress -Depth 3) + "`n"
    [System.IO.File]::AppendAllText($failLog, $line, $utf8)
    Push-FailureLog
    if ($null -eq $exitCode) { exit 1 }
}
exit $exitCode
