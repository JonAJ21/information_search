#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Building C++ modules..."

python3 -c "import pybind11; print(f'Pybind11: {pybind11.__version__}')"

PYBIND11_INCLUDES=$(python3 -m pybind11 --includes)
PYTHON_EXT_SUFFIX=$(python3-config --extension-suffix)
PYTHON_LIBS=$(python3-config --libs)

echo "Python extension suffix: $PYTHON_EXT_SUFFIX"
echo "Python libs: $PYTHON_LIBS"

PYTHON_INCLUDE_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
PYTHON_LIBRARY_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")

echo "Building text_processor_cpp..."
c++ -O3 -Wall -shared -std=c++17 -fPIC \
    ${PYBIND11_INCLUDES} \
    -I${PYTHON_INCLUDE_DIR} \
    text_processor.cpp \
    -L${PYTHON_LIBRARY_DIR} ${PYTHON_LIBS} \
    -o text_processor_cpp${PYTHON_EXT_SUFFIX}

echo "Building boolean_index_cpp..."
c++ -O3 -Wall -shared -std=c++17 -fPIC \
    ${PYBIND11_INCLUDES} \
    -I${PYTHON_INCLUDE_DIR} \
    boolean_index.cpp \
    -L${PYTHON_LIBRARY_DIR} ${PYTHON_LIBS} \
    -o boolean_index_cpp${PYTHON_EXT_SUFFIX}

echo "C++ modules have been built!"