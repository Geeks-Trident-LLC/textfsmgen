# ⚙️ Installing PowerShell 7 (pwsh)

PowerShell 7+ (`pwsh`) is recommended for all scripts in this project.

---

## 1. Check your current PowerShell version
```powershell
$PSVersionTable.PSVersion
```
- **Major = 5** → Windows PowerShell (older)
- **Major = 7** → PowerShell 7+ (recommended)

---

## 2. Check if `pwsh` is installed
```powershell
pwsh --version
```
If you see an error, PowerShell 7 is not installed.

---

## 3. Install PowerShell 7

### Windows (winget)
```powershell
winget install Microsoft.PowerShell
```

### macOS (Homebrew)
```bash
brew install --cask powershell
```

### Linux (Ubuntu example)
```bash
sudo apt-get update
sudo apt-get install -y powershell
```

---

## 4. Verify installation
```powershell
pwsh --version
```
Expected:
```
PowerShell 7.x.x
```

If `pwsh` works, use:
```powershell
pwsh scripts/<file>.ps1
```

If not, fallback to:
```powershell
powershell scripts/<file>.ps1
```