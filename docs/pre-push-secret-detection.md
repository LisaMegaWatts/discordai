# Git Pre-Push Secret Detection

## Purpose and Overview

The pre-push hook is designed to prevent accidental commits of sensitive information (such as API keys, passwords, or secrets) to the repository. It automatically scans staged changes for potential secrets before allowing a push to proceed.

## How the Hook Works

- When you run `git push`, the pre-push hook is triggered.
- The hook scans the changes for patterns commonly associated with secrets (e.g., keys, tokens, passwords).
- If a secret is detected, the push is blocked, and a warning message is displayed.
- You must remove the detected secret before retrying the push.

## Platform Limitations

- **Windows:** The hook requires Git Bash or WSL (Windows Subsystem for Linux) to function correctly. Native Windows Command Prompt or PowerShell are not supported.
- **Linux/macOS:** Fully supported.

## Enabling the Pre-Push Hook

1. Ensure you have Git Bash or WSL installed on Windows.
2. Copy the provided `pre-push` script to `.git/hooks/pre-push` in your repository.
3. Make the hook executable:
   ```bash
   chmod +x .git/hooks/pre-push
   ```

## Testing the Hook

- Try to commit and push a file containing a dummy secret (e.g., `test_secret.txt`).
- The push should be blocked, and you should see a warning message.
- Remove the secret and retry the push to confirm normal operation.

## Troubleshooting

- **Hook not running:** Ensure the script is in `.git/hooks/pre-push` and is executable.
- **No warning on secret:** Verify you are using Git Bash/WSL on Windows.
- **False positives:** Review the hook's pattern matching and adjust as needed.

## Integrating External Secret Scanning Tools

For enhanced security, consider integrating external tools such as:

- [GitGuardian](https://www.gitguardian.com/)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)
- [Gitleaks](https://github.com/gitleaks/gitleaks)

These tools can be added to your CI/CD pipeline or run locally for more comprehensive secret detection.

## Recommendations

- Always review changes for secrets before pushing.
- Use external scanning tools for additional protection.
- Educate team members about the risks of committing secrets.
