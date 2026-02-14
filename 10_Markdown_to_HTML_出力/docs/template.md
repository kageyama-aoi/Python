# Title

## Summary
- Purpose:
- Audience:
- Last updated:

## Quick Links
- Related doc: [Doc Name](../md/example.md)
- Script: [md_helper.ps1](../md_helper.ps1)

## Notes
- Item 1
- Item 2

## References
- Link: [Example](https://example.com)

## Snippets
```powershell
# Link snippet from current directory
.\md_helper.ps1 -Mode link -TargetPath ".\docs\template.md"

# Link snippet for a specific markdown file location
.\md_helper.ps1 -Mode link -TargetPath ".\picture\sample.png" -FromPath ".\md\guide.md"

# Image snippet and copy to clipboard
.\md_helper.ps1 -Mode image -TargetPath ".\picture\sample.png" -FromPath ".\md\guide.md" -Copy
```
