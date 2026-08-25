# Push backend/ to a Hugging Face Space via git subtree.
# Usage:
#   .\scripts\push-hf-space.ps1 -SpaceOwner XENO2410 -SpaceName vartalaap-api
#
# One-time prereqs:
#   - Create the Space at https://huggingface.co/new-space (choose Docker SDK).
#   - Create a personal access token at https://huggingface.co/settings/tokens
#     with "Write" scope and export it as $env:HF_TOKEN (or paste at the prompt).

param(
    [Parameter(Mandatory=$true)][string]$SpaceOwner,
    [Parameter(Mandatory=$true)][string]$SpaceName,
    [string]$Branch = "main",
    [string]$Prefix = "backend"
)

$ErrorActionPreference = "Stop"

if (-not $env:HF_TOKEN) {
    $secure = Read-Host "Hugging Face write token (hf_...)" -AsSecureString
    $env:HF_TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    )
}

$remoteName = "hf-$SpaceName"
$remoteUrl  = "https://$SpaceOwner`:$env:HF_TOKEN@huggingface.co/spaces/$SpaceOwner/$SpaceName"

Write-Host "→ Ensuring remote '$remoteName' points at the Space" -ForegroundColor Cyan
git remote remove $remoteName 2>$null | Out-Null
git remote add $remoteName $remoteUrl

Write-Host "→ Pushing '$Prefix' subtree to '$remoteName/$Branch'" -ForegroundColor Cyan
git subtree push --prefix=$Prefix $remoteName $Branch

Write-Host "`n✓ Done. Space is building at:"
Write-Host "  https://huggingface.co/spaces/$SpaceOwner/$SpaceName"
Write-Host "`nRemove the tokenized remote when finished:"
Write-Host "  git remote remove $remoteName"
