pkg_path="$(cd "$(dirname "$BASH_SOURCE")" && pwd -P)/"
if [[ $PYTHONPATH = *"${pkg_path}"* ]]; then
    echo "$pkg_path already part of PYTHONPATH"
else
    export PYTHONPATH="$PYTHONPATH:${pkg_path}"
    echo "$pkg_path added to PYTHONPATH"
    echo "To import, add 'import LexTools'"
fi
