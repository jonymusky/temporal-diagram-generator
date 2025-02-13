
PROGRAM         := generate-mermaid.py
HISTORY_URL     := https://raw.githubusercontent.com/temporal-sa/temporal-money-transfer-java/refs/heads/main/workflowHistories/happy-path-ui-decoded.json
HISTORY_FILE    := workflows_history/happy_path.json
MERMAID_FILE    := mermaid_diagrams/happy_path.mmd

help:
	@awk 'BEGIN {FS = ":.*?## "} /^[^: ]+:.*?## / {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup-testing: ## prepare test env
	mkdir -p workflows_history mermaid_diagrams
	[ -f "$(HISTORY_FILE)" ] || curl -sL $(HISTORY_URL) > $(HISTORY_FILE)

test: setup-testing  ## run tests
	python $(PROGRAM) -f  $(HISTORY_FILE) | grep -q '^graph TD;'
	rm -f $(MERMAID_FILE)
	python $(PROGRAM) && grep -q '^graph TD;' $(MERMAID_FILE)
	rm -f $(MERMAID_FILE)
	python $(PROGRAM) -w workflows_history -m mermaid_diagrams && grep -q '^graph TD;' $(MERMAID_FILE)


