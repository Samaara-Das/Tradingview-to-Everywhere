# setup_startup.ps1
# Registers TTE.exe as a Windows Task Scheduler task that:
#   - Starts automatically when the current user logs on
#   - Runs in the background
#   - Stops when the user logs off / PC shuts down
#
# Usage (run as Administrator in PowerShell):
#   .\setup_startup.ps1
#
# To remove:
#   .\setup_startup.ps1 -Remove

param(
    [switch]$Remove
)

$TaskName = "TTE_AutoStart"
$ExePath = "C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere\dist\TTE.exe"

if ($Remove) {
    Write-Host "Removing scheduled task '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Done. TTE will no longer start automatically." -ForegroundColor Green
    exit 0
}

# Validate exe exists
if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: TTE.exe not found at: $ExePath" -ForegroundColor Red
    Write-Host "Please build the exe first with: pyinstaller --name TTE --onefile --windowed tte_gui.py"
    exit 1
}

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create the task
$Action = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory (Split-Path $ExePath)
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0)  # No time limit (runs indefinitely)

# StopIfGoingOnBatteries is disabled by AllowStartIfOnBatteries above
# ExecutionTimeLimit of 0 means "run forever"

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "TradingView to Everywhere - Auto-start in maintain-only mode on login" `
    -RunLevel Limited

Write-Host ""
Write-Host "SUCCESS: TTE.exe is now registered to start automatically on login." -ForegroundColor Green
Write-Host "  Task name : $TaskName" -ForegroundColor Cyan
Write-Host "  Exe path  : $ExePath" -ForegroundColor Cyan
Write-Host "  Trigger   : At logon for user $env:USERNAME" -ForegroundColor Cyan
Write-Host ""
Write-Host "To remove later, run:  .\setup_startup.ps1 -Remove" -ForegroundColor Yellow
