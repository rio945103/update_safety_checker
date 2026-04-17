import subprocess
import json


POWERSHELL_SCRIPT = """
$updates = Get-WindowsUpdate
$result = for ($i = 0; $i -lt $updates.Count; $i++) {
    $u = $updates[$i]
    [PSCustomObject]@{
        KB = [string]$u.KB
        Title = [string]$u.Title
        Size = [string]$u.Size
        Description = [string]$u.Description
        RebootRequired = [bool]$u.RebootRequired
        MsrcSeverity = [string]$u.MsrcSeverity
        LastDeploymentChangeTime = [string]$u.LastDeploymentChangeTime
    }
}
$result | ConvertTo-Json
"""


def fetch_local_windows_updates() -> list[dict]:
    result = subprocess.run(
        ["powershell", "-Command", POWERSHELL_SCRIPT],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"PowerShell error: {result.stderr}")

    output = result.stdout.strip()

    if not output:
        return []

    parsed = json.loads(output)

    if isinstance(parsed, dict):
        parsed = [parsed]

    return parsed