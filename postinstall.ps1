# Post-Installation Script for Medical Office Management Application
# Version: 1.0.0
# Date: $(Get-Date -Format "yyyy-MM-dd")

# Check if .NET 5.0 or later is installed
$dotnetVersion = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\NET Framework\').Version
If ($dotnetVersion -lt "5.0.0") {
    Write-Error "This application requires .NET 5.0 or later. Please install .NET first."
    Exit 1
}

# Verify Python 3.10 or later is installed
$pythonVersion = (python --version 2>&1).Trim()
If ($pythonVersion -notmatch "Python 3\.10") {
    Write-Error "This application requires Python 3.10 or later. Please install Python first."
    Exit 1
}

# Create a registry key for the application
New-Item -Path "HKLM:\SOFTWARE\Medical Office\" -Force
New-ItemProperty -Path "HKLM:\SOFTWARE\Medical Office\" -Name "InstalledVersion" -Value "1.0.0" -PropertyType String

# Set up application data directory
$path = "C:\ProgramData\Medical Office"
If (!(Test-Path $path)) {
    New-Item -Path $path -ItemType Directory
}
$acl = Get-Acl $path
$acl.SetAccessRule("Everyone", "FullControl")
Set-Acl $path $acl

# Create a shortcut on the desktop
$shortcutPath = "$env:USERPROFILE\Desktop\Medical Office.lnk"
$targetPath = "C:\path\to\your\application.py"  # Replace with actual path
$arguments = ""

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.Arguments = $arguments
$shortcut.IconLocation = "assets\logo.ico"  # Replace with actual icon path
$shortcut.Save()

try {
    # Additional installation steps if needed
    # Example: Copying configuration files
    Copy-Item -Path "config.json" -Destination "C:\ProgramData\Medical Office\" -Force
} catch {
    Write-Error "An error occurred during installation: $_"
    Exit 1
} finally {
    # Cleanup code if necessary
}

Write-Host "Installation completed successfully!" -ForegroundColor Green
