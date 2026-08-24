# Security, Configuration, and Cost Controls

## Secret handling

- `.env` is local and ignored. `.env.example` contains names and safe placeholders only.
- Never commit database passwords, Databricks tokens, Power BI credentials, connection strings with secrets, or private keys.
- Use `git check-ignore .env` before the first commit.
- If a secret reaches Git, assume it is compromised: revoke/rotate it first, then remove history using an approved method. Deleting the visible line is not enough.
- Use Databricks secret management or supported cloud identities for Track B. Do not display secret values in notebook output.
- Redact logs and screenshots.

## Least privilege

| Identity | Minimum learning access |
|---|---|
| Local source loader | Insert/select in source schemas; no server-admin need after setup |
| Local extractor | Read-only on source tables and watermark metadata |
| Databricks workflow | Read/write on project volume, Bronze/Silver/Gold/quality schemas only |
| Local Gold publisher | Stage/load in warehouse plus audit writes |
| Power BI/analyst | Read-only on `dw` tables or `semantic` views |

Use separate identities in a real environment. Track A may use your local Windows identity for simplicity, but document that this is not a production access model.

## Development versus production configuration

- `config/dev.example.yml` is a template; create `config/dev.yml` locally and ignore it if it contains environment-specific values.
- Use environment variables for secrets.
- Keep catalog/schema/database names parameterized.
- Development can use safe full reloads; production usually needs tested incremental strategies and deployment controls.
- The destructive reset scripts contain guards. Never remove the guard in shared environments.

## Synthetic PII practice

Although all identities are fictional, mask or hide names/emails in executive pages, limit detail access, and classify fields. This builds habits without using real people.

## Cost-aware choices

- Generate `quick` while debugging, `small` after logic works, and `portfolio` only for a final performance demonstration.
- Free/community offerings have quota and feature limits that can change; verify the current official page before relying on them.
- Use serverless/job compute only for active tasks; avoid repeated blind retries.
- Stop local database services when you no longer need them if your computer resources are constrained.
- Import mode in Power BI is the default Track A choice; refresh intentionally.
- Track B can create charges for databases, compute, storage, egress, networking, and Power BI capacity/licensing. Set budgets/alerts before creating resources.

## Secret-scanning checklist

- [ ] `.env` is ignored and absent from `git ls-files`.
- [ ] No password/token/private-key pattern appears in tracked text.
- [ ] Notebook outputs contain no credentials.
- [ ] Screenshots hide server details and account email where unnecessary.
- [ ] GitHub Actions uses encrypted repository/environment secrets only when needed.
- [ ] Public sample data is quick-scale and fictional.
- [ ] Connection test logs redact passwords.
- [ ] Any exposed credential was revoked, not merely deleted from a file.
