sphinx-apidoc --implicit-namespaces -e -f -o . ../fram && sphinx-build -c ./docs_source . ../docs
rm -f -- fram.*
