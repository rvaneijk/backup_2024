function Get-MirroredOneDriveSyncStatus {
    $mirrorPairs = @(
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\BAK"; Mirror = "E:\mnt\aws.local" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\Datakluis"; Mirror = "E:\Datakluis" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\Onze cd's"; Mirror = "E:\Onze cd's" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\Onze foto's"; Mirror = "E:\Onze foto's" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\Papers, presentations, webinars etc"; Mirror = "E:\Papers, presentations, webinars etc" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\PhD_archive"; Mirror = "E:\PhD_archive" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\Tools"; Mirror = "E:\Tools" },
        @{ OneDrive = "C:\mnt\OneDrive - 240808\OneDrive - Blaeu Privacy Response Team B.V\Users"; Mirror = "E:\Users" }
    )

    $timeTolerance = [TimeSpan]::FromSeconds(2)
    $cutoffDate = (Get-Date).AddDays(-7)

    foreach ($pair in $mirrorPairs) {
        Write-Host "Checking mirrored directories:" -ForegroundColor Cyan
        Write-Host "OneDrive: $($pair.OneDrive)" -ForegroundColor Yellow
        Write-Host "Mirror  : $($pair.Mirror)" -ForegroundColor Yellow

        $oneDriveFiles = Get-ChildItem -Path $pair.OneDrive -Recurse -File -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -gt $cutoffDate -and $_.FullName -notmatch '\.git\\' }
        $mirrorFiles = Get-ChildItem -Path $pair.Mirror -Recurse -File -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -gt $cutoffDate -and $_.FullName -notmatch '\.git\\' }

        $oneDriveDict = @{}
        $oneDriveFiles | ForEach-Object { $oneDriveDict[$_.FullName.Replace($pair.OneDrive, "")] = $_ }

        $mirrorDict = @{}
        $mirrorFiles | ForEach-Object { $mirrorDict[$_.FullName.Replace($pair.Mirror, "")] = $_ }

        $missingInOneDrive = @()
        $missingInMirror = @()
        $mismatchedFiles = @()

        foreach ($key in $oneDriveDict.Keys) {
            if (-not $mirrorDict.ContainsKey($key)) {
                $missingInMirror += $key
            } else {
                $oneDriveFile = $oneDriveDict[$key]
                $mirrorFile = $mirrorDict[$key]
                if ($oneDriveFile.Length -ne $mirrorFile.Length) {
                    $mismatchedFiles += @{
                        Path = $key
                        Reason = "Size mismatch"
                        OneDriveSize = $oneDriveFile.Length
                        MirrorSize = $mirrorFile.Length
                    }
                }
                elseif ([Math]::Abs(($oneDriveFile.LastWriteTime - $mirrorFile.LastWriteTime).TotalSeconds) -gt $timeTolerance.TotalSeconds) {
                    $mismatchedFiles += @{
                        Path = $key
                        Reason = "Time mismatch"
                        OneDriveTime = $oneDriveFile.LastWriteTime
                        MirrorTime = $mirrorFile.LastWriteTime
                    }
                }
            }
        }

        foreach ($key in $mirrorDict.Keys) {
            if (-not $oneDriveDict.ContainsKey($key)) {
                $missingInOneDrive += $key
            }
        }

        Write-Host "Comparison results:" -ForegroundColor Magenta
        Write-Host "  OneDrive files: $($oneDriveDict.Count)" -ForegroundColor Cyan
        Write-Host "  Mirror files  : $($mirrorDict.Count)" -ForegroundColor Cyan

        if ($missingInOneDrive -or $missingInMirror -or $mismatchedFiles) {
            Write-Host "Discrepancies detected!" -ForegroundColor Red
            
            if ($missingInOneDrive) {
                Write-Host "Files in Mirror but not in OneDrive:" -ForegroundColor Red
                $missingInOneDrive | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
            if ($missingInMirror) {
                Write-Host "Files in OneDrive but not in Mirror:" -ForegroundColor Red
                $missingInMirror | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
            if ($mismatchedFiles) {
                Write-Host "Mismatched files:" -ForegroundColor Red
                $mismatchedFiles | ForEach-Object {
                    Write-Host "  $($_.Path)" -ForegroundColor Gray
                    Write-Host "    Reason: $($_.Reason)" -ForegroundColor Gray
                    if ($_.Reason -eq "Size mismatch") {
                        Write-Host "    OneDrive size: $($_.OneDriveSize) bytes" -ForegroundColor Gray
                        Write-Host "    Mirror size  : $($_.MirrorSize) bytes" -ForegroundColor Gray
                    } elseif ($_.Reason -eq "Time mismatch") {
                        Write-Host "    OneDrive time: $($_.OneDriveTime)" -ForegroundColor Gray
                        Write-Host "    Mirror time  : $($_.MirrorTime)" -ForegroundColor Gray
                    }
                }
            }
        } else {
            Write-Host "No discrepancies found between OneDrive and Mirror." -ForegroundColor Green
        }

        Write-Host "`n"
    }

    # Check OneDrive logs for any relevant error messages
    $logPath = Join-Path $env:LOCALAPPDATA "Microsoft\OneDrive\logs\Business1"
    $recentLogs = Get-ChildItem -Path $logPath -Filter "*.odl" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

    Write-Host "Checking recent OneDrive logs for error messages..." -ForegroundColor Yellow
    foreach ($log in $recentLogs) {
        $content = Get-Content $log.FullName -Raw
        if ($content -match "(?smi)Error|Exception|Failed") {
            Write-Host "Found potential errors in log file: $($log.Name)" -ForegroundColor Red
            $content -split "`n" | Select-String -Pattern "Error|Exception|Failed" | 
                Where-Object { $_ -notmatch '\.git' } |
                ForEach-Object {
                    Write-Host "  $_" -ForegroundColor Gray
                }
        }
    }
}

# Run the function
Get-MirroredOneDriveSyncStatus