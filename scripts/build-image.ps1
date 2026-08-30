$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$drive = "X:"
$mapped = (subst | Select-String -Pattern "^X:\\:\s*=>")
$createdMapping = $false

try {
    if (-not $mapped) {
        subst $drive $projectRoot
        $createdMapping = $true
    }

    docker build --tag kb-app:day7 "$drive\"
    if ($LASTEXITCODE -ne 0) {
        throw "Docker image build failed with exit code $LASTEXITCODE"
    }
}
finally {
    if ($createdMapping) {
        subst $drive /D | Out-Null
    }
}
