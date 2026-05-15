# Convenience targets for the da_vinci integration test suite.
#
# All targets run from the repo root (they cd in here automatically).
# Required: AWS credentials in the environment, Docker running, CDK
# bootstrap already performed for the target account/region.

REGION ?= us-east-1

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make test         — full deploy → test → destroy"
	@echo "  make test-keep    — deploy & test; leave deployed afterward"
	@echo "  make test-reuse   — reuse the previous deployment (set DA_VINCI_IT_INSTALL_ID)"
	@echo "  make synth        — synth the main app + sidecar, no deploy"
	@echo "  make destroy      — destroy a deployment named by DA_VINCI_IT_INSTALL_ID"

.PHONY: test
test:
	uv run pytest --region $(REGION)

.PHONY: test-keep
test-keep:
	uv run pytest --region $(REGION) --keep

.PHONY: test-reuse
test-reuse:
	uv run pytest --region $(REGION) --reuse --keep

.PHONY: synth
synth:
	cd app && DA_VINCI_IT_DEPLOYMENT_ID=$${DA_VINCI_IT_INSTALL_ID:-it-synthcheck} uv run cdk synth --quiet
	cd sidecar && DA_VINCI_IT_DEPLOYMENT_ID=$${DA_VINCI_IT_INSTALL_ID:-it-synthcheck} uv run cdk synth --quiet

.PHONY: destroy
destroy:
	@test -n "$(DA_VINCI_IT_INSTALL_ID)" || (echo "DA_VINCI_IT_INSTALL_ID required" && exit 1)
	cd sidecar && DA_VINCI_IT_DEPLOYMENT_ID=$(DA_VINCI_IT_INSTALL_ID) uv run cdk destroy --all --force
	cd app && DA_VINCI_IT_DEPLOYMENT_ID=$(DA_VINCI_IT_INSTALL_ID) uv run cdk destroy --all --force
