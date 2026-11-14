Get-ChildItem -File -Filter *.jpg | ForEach-Object {
    $tmp = "$($_.FullName).tmp.jpg"

    magick $_.FullName `
        -background white `
        -alpha remove `
        -alpha off `
        -quality 82 `
        $tmp

    if ($LASTEXITCODE -eq 0) {
        Move-Item -Force $tmp $_.FullName
        Write-Host "OK : $($_.Name)"
    }
}