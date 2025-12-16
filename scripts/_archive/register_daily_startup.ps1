# GARAM Daily Startup - Windows Task Scheduler
# Register this script to run daily at 09:00 KST

Write-Host "=" * 60
Write-Host "GARAM Daily Startup Scheduler Registration"
Write-Host "=" * 60

# Configuration
$TaskName = "GARAM_Daily_Startup"
$TaskDescription = "GARAM 자동매매 시스템 일일 시작 (09:00 KST)"

# Paths (adjust if needed)
$Python32Path = "C:\Python32\python.exe"  # 32-bit Python for Kiwoom
$Python64Path = "python"  # 64-bit Python (system default)
$GaramRoot = "c:\garam\garam"

# Scripts
$Script1_Login = "$GaramRoot\scripts\kiwoom_auto_login.py"
$Script2_Wait = "$GaramRoot\scripts\wait_for_kiwoom.py"
$Script3_Server = "$GaramRoot\api\server.py"

# Check if 32-bit Python exists
if (-not (Test-Path $Python32Path)) {
    Write-Host "⚠️  WARNING: 32-bit Python not found at: $Python32Path"
    Write-Host "   Kiwoom API requires 32-bit Python!"
    Write-Host "   Please install 32-bit Python and update" the path in this script."
    Write-Host ""
    $Python32Path = Read-Host "Enter 32-bit Python path (or press Enter to skip)"
    if ([string]::IsNullOrWhiteSpace($Python32Path)) {
        Write-Host "❌ Skipping Kiwoom auto-login setup"
        Write-Host "   You will need to login manually"
        $Python32Path = $null
    }
}

# Create Task Actions
$actions = @()

# Action 1: Kiwoom Auto Login (32-bit Python)
if ($Python32Path) {
    $action1 = New-ScheduledTaskAction -Execute $Python32Path `
        -Argument $Script1_Login `
        -WorkingDirectory $GaramRoot
    $actions += $action1
    Write-Host "✅ Action 1: Kiwoom Auto Login (32-bit)"
}

# Action 2: Wait for Kiwoom (64-bit Python)
$action2 = New-ScheduledTaskAction -Execute $Python64Path `
    -Argument "$Script2_Wait --max-wait 10" `
    -WorkingDirectory $GaramRoot
$actions += $action2
Write-Host "✅ Action 2: Wait for Kiwoom Ready"

# Action 3: Start Dashboard Server (64-bit Python)
$action3 = New-ScheduledTaskAction -Execute $Python64Path `
    -Argument $Script3_Server `
    -WorkingDirectory $GaramRoot
$actions += $action3
Write-Host "✅ Action 3: Start Dashboard Server"

# Create Trigger: Daily at 09:00 KST
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
Write-Host "✅ Trigger: Daily at 09:00 KST"

# Create Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12)

# Create Principal (Run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

# Register Task
Write-Host ""
Write-Host "Registering scheduled task..."

try {
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Host "⚠️  Task '$TaskName' already exists. Updating..."
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Register new task
    Register-ScheduledTask -TaskName $TaskName `
        -Description $TaskDescription `
        -Action $actions `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal
    
    Write-Host "=" * 60
    Write-Host "✅ SUCCESS: Daily startup task registered!"
    Write-Host "=" * 60
    Write-Host ""
    Write-Host "Task Name: $TaskName"
    Write-Host "Schedule: Daily at 09:00 KST"
    Write-Host ""
    Write-Host "To view task:"
    Write-Host "   Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To run task manually (test):"
    Write-Host "   Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To disable task:"
    Write-Host "   Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To remove task:"
    Write-Host "   Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host "=" * 60
    
} catch {
    Write-Host "=" * 60
    Write-Host "❌ ERROR: Failed to register task"
    Write-Host "=" * 60
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator!"
    exit 1
}

# Ask if user wants to run a test
Write-Host ""
$test = Read-Host "Do you want to test the task now? (y/N)"
if ($test -eq "y" -or $test -eq "Y") {
    Write-Host ""
    Write-Host "🧪 Running test (without Kiwoom login)..."
    Write-Host "   This will:"
    Write-Host "   1. Skip Kiwoom login (using --skip flag)"
    Write-Host "   2. Start dashboard server"
    Write-Host "   3. You can access dashboard at http://localhost:5000"
    Write-Host ""
    
    # Run waiter with skip flag (for testing)
    & $Python64Path $Script2_Wait --skip
    
    # Start server
    Write-Host ""
    Write-Host "Starting dashboard server..."
    Write-Host "Press Ctrl+C to stop"
    & $Python64Path $Script3_Server
}

Write-Host ""
Write-Host "✅ Setup complete!"
