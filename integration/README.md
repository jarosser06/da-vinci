# Da Vinci — Real-AWS Integration Test Framework

A self-contained, behavior-driven (pytest-bdd) regression suite for the
`da_vinci` and `da_vinci-cdk` packages. It deploys a real Da Vinci application
to AWS, exercises the event bus / exception trap / REST service / ORM /
sidecar functionality, validates with **exact** assertions against the
deployed AWS resources, then tears the application down.

## Components

```
integration/
├── app/         # The CDK application under test (event bus, exception trap, REST, ORM)
├── sidecar/     # A SideCarApplication attached to the main app
├── lib/         # Validation library (boto3 clients, event publisher, response/exception inspectors)
├── features/    # Gherkin .feature files
└── tests/       # pytest-bdd step definitions
```

## Prerequisites

- AWS credentials with permission to deploy CDK stacks (the suite uses your
  default profile/region; override with `AWS_PROFILE` and `AWS_REGION`)
- CDK bootstrap performed for the target account/region:
  `runbook cdk-bootstrap` (or `cdk bootstrap`)
- Docker running locally (CDK builds container images for the Lambda functions)

## Running

From the repo root:

```bash
# Full run: deploy → test → destroy
uv run pytest integration/tests -v

# Leave deployment alive after run (for inspection / troubleshooting)
uv run pytest integration/tests -v --keep

# Reuse a previous deployment (paired with the install id from the prior run)
DA_VINCI_IT_INSTALL_ID=it-abc12345 uv run pytest integration/tests -v --reuse --keep
```

CLI flags (declared in `integration/tests/conftest.py`):

| Flag       | Purpose                                                                |
| ---------- | ---------------------------------------------------------------------- |
| `--keep`   | Skip `cdk destroy` at the end of the session                           |
| `--reuse`  | Skip `cdk deploy` at the start, reuse `$DA_VINCI_IT_INSTALL_ID`        |
| `--region` | Override AWS region (default: `$AWS_REGION` or `us-east-1`)            |

## Feature coverage

| Feature                          | Validates                                                  |
| -------------------------------- | ---------------------------------------------------------- |
| `event_bus.feature`              | publish → subscriber executes → `SUCCESS` row in responses |
| `exception_trap.feature`         | publish → failing handler → exact `TrappedException` row   |
| `callback_chain.feature`         | callback_event_type chains via `previous_event_id`         |
| `rest_service_orm.feature`       | SigV4 REST + ORM read/write + global settings              |
| `sidecar.feature`                | SideCarApplication deploys and reaches parent resources    |

Assertions use **exact equality** (`==`) on response status, failure reason,
exception payload, and chained event metadata — not `in` / substring checks.

## How it works

1. `tests/conftest.py` defines a session-scoped `deployment` fixture.
2. The fixture builds a unique `deployment_id` (`it-<8-hex>`), shells out to
   `runbook cdk-deploy --all` against `app/app.py` (and then `sidecar/app.py`).
3. Step definitions in `tests/test_*.py` use `lib.events.publish`,
   `lib.responses.wait_for_response`, `lib.exceptions.wait_for_trapped`,
   `lib.rest.invoke`, and `lib.tables.get_app_item` to drive and assert.
4. On session teardown (unless `--keep`), shells out to `runbook cdk-destroy
   --all` for both apps.
