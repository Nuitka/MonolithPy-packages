<#
verify-static-windows.ps1 -Paths dir1[,dir2,...]

Assert that the Windows build artifacts are fully static (/MT).

MonolithPy packages ship as relocatable .obj / .lib that are linked into the
monolithic interpreter; there are no dynamic modules in a shipped wheel (that
"no .dll/.pyd present" rule is enforced by verify_artifacts.py). This script
covers the other half: every object / static lib must request the STATIC CRT
(LIBCMT / LIBCPMT). A /DEFAULTLIB directive naming the dynamic CRT (MSVCRT /
MSVCPRT and their debug variants) means the object was compiled /MD -- a single
/MD object poisons the whole /MT link (CRT conflict, LNK4098) and is a failure.

Locates dumpbin on PATH, else via vswhere (no active MSVC environment required).
#>
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string[]]$Paths)

$ErrorActionPreference = 'Stop'

function Get-Dumpbin {
  $c = Get-Command dumpbin -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
  if (Test-Path $vswhere) {
    $vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($vs) {
      $db = Get-ChildItem "$vs\VC\Tools\MSVC\*\bin\Hostx64\x64\dumpbin.exe" -ErrorAction SilentlyContinue |
            Select-Object -First 1
      if ($db) { return $db.FullName }
    }
  }
  throw "dumpbin not found (set up the MSVC environment first)."
}
$dumpbin = Get-Dumpbin

# Dynamic-CRT /DEFAULTLIB names: their presence means the object is /MD, not /MT.
$crtLib = '^(msvcrt|msvcprt|msvcrtd|msvcprtd)$'

$violations = New-Object System.Collections.Generic.List[string]
$scanned = 0

foreach ($root in $Paths) {
  if (-not (Test-Path $root)) { continue }
  $files = Get-ChildItem -Path $root -Recurse -File -Include *.lib,*.obj -ErrorAction SilentlyContinue
  foreach ($f in $files) {
    $scanned++
    $out = & $dumpbin /nologo /directives $f.FullName 2>$null
    foreach ($line in $out) {
      if ($line -match '/DEFAULTLIB:"?([A-Za-z0-9_.-]+)"?') {
        $lib = $Matches[1].ToLower() -replace '\.lib$',''
        if ($lib -match $crtLib) {
          $violations.Add("$($f.FullName): dynamic-CRT /DEFAULTLIB:$lib (compiled /MD, not /MT)")
        }
      }
    }
  }
}

if ($violations.Count -gt 0) {
  Write-Host "verify-static-windows: FAIL -- objects compiled /MD (not full /MT):"
  $violations | Sort-Object -Unique | ForEach-Object { Write-Host "    $_" }
  exit 1
}

Write-Host "verify-static-windows: OK -- $scanned .lib/.obj are full /MT (static CRT)"
