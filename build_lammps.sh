#!/bin/bash

setvar() {
    while [[ $# -gt 0 ]]; do
        export $1
        shift
    done
}

ml nvhpc nvpl

setvar "$@"
: ${TAG:="grace"}

mkdir lammps-build-${TAG}
cd lammps-build-${TAG}

cmake -DBUILD_OMP=no -DPKG_SPIN=yes -DPKG_MANYBODY=yes ../lammps/cmake

cmake --build . -j$(nproc)
