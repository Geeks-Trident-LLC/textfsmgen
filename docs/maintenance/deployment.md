# 🟪 Deployment Maintenance

Final release and deployment tasks.

```powershell
pwsh scripts/validate-all.ps1
pwsh scripts/pack-release.ps1
pwsh scripts/release.ps1
pwsh scripts/release-draft.ps1 -Tag vX.Y.Z
pwsh scripts/release-finalize.ps1 -Tag vX.Y.Z
pwsh scripts/release-notify.ps1 -Tag vX.Y.Z -SlackWebhook <url>
```