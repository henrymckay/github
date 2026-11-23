# Dependencies

The plan is [`PLAN.md`](PLAN.md).

## Accounts and services

- **GitHub repository `henrymckay/github`** — holds the code on branch `feat/reading-list`; running cost $0; removed by deleting the branch.

## Credentials

None.

## Tools

- **uv 0.11 or later** — needed by the build and the run; installed with the [standalone installer](https://docs.astral.sh/uv/getting-started/installation/).
- **Python 3.15** — needed by the run; installed by `uv` on first run.
- **Chromium with Playwright** — used by the build for screenshots only; preinstalled in the cloud session, not needed to run the app.

## Connectors, plugins and skills

- **House plugins** (`design-project`, `maintain-plugin`, `manage-project`, `run-project`, `structure-app`, `write-code`) — loaded by the session's start-up hook from the pinned commit; relied on by the plan and the build.

## Packages

The lock file lists them.
The Inter font (`src/reading_list/data/drive/static/inter.woff2`) comes from `@fontsource-variable/inter` 5.2.5 on npm, under the SIL Open Font License 1.1.
