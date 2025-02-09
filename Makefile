.PHONY: lint format

#################################################################################
# GLOBALS                                                                       #
#################################################################################

LINE_LENGTH = 100
PROJECT_NAME = src

lint:
	isort --check $(PROJECT_NAME)
	black --line-length $(LINE_LENGTH) --check $(PROJECT_NAME)
	mypy $(PROJECT_NAME)
	flake8 $(PROJECT_NAME) --max-line-length $(LINE_LENGTH)

format:
	isort $(PROJECT_NAME)
	black --line-length $(LINE_LENGTH) $(PROJECT_NAME)
