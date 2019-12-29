PY_FILES= find . -type f -not -path '*/\.*' | grep -i '.*[.]py$$' 2> /dev/null

entr_warn: 
	@echo "----------------------------------------------------------"
	@echo "     ! File watching functionality non-operational !      "
	@echo "                                                          "
	@echo "Install entr(1) to automatically run tasks on file change."
	@echo "See http://entrproject.org/                               "
	@echo "----------------------------------------------------------"

isort:
	isort `${PY_FILES}`

black:
	black `${PY_FILES}` --skip-string-normalization

flake8:
	flake8 fabric_helpers

watch_flake8:
	if command -v entr > /dev/null; then ${PY_FILES} | entr -c $(MAKE) flake8; else $(MAKE) flake8 entr_warn; fi
