param(
    [string]$Title = "Claude Code",
    [string]$Message = "Response ready"
)

Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.Visible = $true
$notification.ShowBalloonTip(5000, $Title, $Message, [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 6
$notification.Dispose()
