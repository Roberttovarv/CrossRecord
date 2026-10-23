# CrossRecord local development commands (Windows / PowerShell).
# Install GNU Make to use these targets, or invoke the referenced .ps1 scripts
# directly from PowerShell.

.PHONY: mongo-up mongo-down mongo-status seed-catalog seed-demo seed test-integration

mongo-up:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_mongo.ps1 -Action up

mongo-down:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_mongo.ps1 -Action down

mongo-status:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_mongo.ps1 -Action status

seed-catalog:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/seed_local.ps1 -Action catalog

seed-demo:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/seed_local.ps1 -Action demo

seed:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/seed_local.ps1 -Action all

test-integration:
	powershell -NoProfile -ExecutionPolicy Bypass -Command "$$env:TEST_MONGO_URI='mongodb://127.0.0.1:27018/?replicaSet=rs0'; pipenv run python -m pytest"
