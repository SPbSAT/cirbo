all:
	mkdir -p cirbo_zip/cirbo
	cp -r cirbo cirbo_zip/cirbo/cirbo
	cp -r data cirbo_zip/cirbo/data
	cp -r extensions cirbo_zip/cirbo/extensions
	cp -r third_party cirbo_zip/cirbo/third_party
	cp -r tests cirbo_zip/cirbo/tests
	cp -r tools cirbo_zip/cirbo/tools
	cp -r tutorial cirbo_zip/cirbo/tutorial
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