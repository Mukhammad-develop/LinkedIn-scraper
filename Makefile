# LinkedIn Scraper Makefile

.PHONY: help install test clean run setup dev-setup

help: ## Show this help message
	@echo "LinkedIn Scraper - Progressive Development"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev-setup: ## Setup development environment
	pip install -r requirements.txt
	cp config.env.example .env
	mkdir -p data logs
	@echo "✅ Development environment setup complete!"

test: ## Run tests
	python -m pytest tests/ -v

test-step1: ## Run Step 1 specific tests
	python tests/test_step1.py

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf data/*.json logs/*.log

run: ## Run the scraper (requires PROFILE_URL env var)
	@if [ -z "$(PROFILE_URL)" ]; then \
		echo "❌ Please provide PROFILE_URL: make run PROFILE_URL=https://linkedin.com/in/username"; \
		exit 1; \
	fi
	python src/main.py --profile-url "$(PROFILE_URL)"

run-demo: ## Run with a demo command (no actual scraping)
	@echo "🚀 LinkedIn Scraper Demo"
	@echo "To run with a real profile:"
	@echo "make run PROFILE_URL=https://linkedin.com/in/username"
	@echo ""
	@echo "Example command:"
	@echo "python src/main.py --profile-url 'https://linkedin.com/in/username' --no-headless"

setup: ## Initial project setup
	@echo "🚀 Setting up LinkedIn Scraper..."
	$(MAKE) dev-setup
	@echo ""
	@echo "📋 Next steps:"
	@echo "1. Edit .env file with your configuration"
	@echo "2. Run: make run PROFILE_URL=https://linkedin.com/in/username"
	@echo "3. Check the data/ folder for results"

lint: ## Run code linting
	@echo "🔍 Running linting (install flake8 first: pip install flake8)"
	flake8 src/ --max-line-length=100 --ignore=E501,W503

format: ## Format code
	@echo "🎨 Formatting code (install black first: pip install black)"
	black src/ tests/

check-deps: ## Check if all dependencies are installed
	@echo "🔍 Checking dependencies..."
	@python -c "import selenium, bs4, requests, pandas, webdriver_manager, fake_useragent; print('✅ All dependencies installed!')"

# Step-specific targets
step1: ## Complete Step 1 setup and test
	@echo "🎯 Step 1: Basic Working Scraper"
	$(MAKE) dev-setup
	$(MAKE) test-step1
	@echo "✅ Step 1 is ready!"
	@echo "Run: make run PROFILE_URL=https://linkedin.com/in/username"

# Development helpers
watch-logs: ## Watch log files (requires tail)
	tail -f logs/*.log

show-structure: ## Show project structure
	@echo "📁 Project Structure:"
	@tree -I '__pycache__|*.pyc|.git|venv|env' . || find . -type f -not -path './.git/*' -not -path './venv/*' -not -path './__pycache__/*' | sort 