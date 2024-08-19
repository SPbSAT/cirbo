all:
	# Build documentation
	cd docs; make html
	# Copy main files
	mkdir -p cirbo_zip/cirbo
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' docs/_build/html/ cirbo_zip/cirbo/docs
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' cirbo cirbo_zip/cirbo/cirbo
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' data cirbo_zip/cirbo/data
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' extensions cirbo_zip/cirbo/extensions
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' third_party cirbo_zip/cirbo/third_party
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' tests cirbo_zip/cirbo/tests
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' tools cirbo_zip/cirbo/tools
	rsync -rv --exclude='*.pyc' --exclude='*.pyo' --exclude='*/__pycache__*' tutorial cirbo_zip/cirbo/tutorial
	cp build.py cirbo_zip/cirbo/build.py
	cp CMakeLists.txt cirbo_zip/cirbo/CMakeLists.txt
	cp poetry.lock cirbo_zip/cirbo/poetry.lock
	cp pyproject.toml cirbo_zip/cirbo/pyproject.toml
	# Rename README files
	cp README_ZIP.md cirbo_zip/cirbo/README.md

	cd cirbo_zip; zip -r cirbo.zip cirbo

.PHONY: rebuild
rebuild:
	$(MAKE) clean
	$(MAKE) all

clean:
	rm -rf cirbo_zip
	rm -f cirbo_zip/cirbo.zip