$input = $input | ConvertFrom-Json
$folder = Split-Path -Leaf $input.workspace.current_dir
$branch = git branch --show-current 2>$null
if ($branch) {
    Write-Host "[$folder] $branch"
} else {
    Write-Host "[$folder]"
}
