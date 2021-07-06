# Copyright 2019-2021 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

NAME ?= gitea
VERSION ?= $(shell cat .rpm_version)-local

SPEC_NAME ?= gitea
RPM_NAME ?= gitea
SPEC_FILE ?= ${SPEC_NAME}.spec
SPEC_VERSION ?= $(shell cat .rpm_version)

.FS_VERSION=$(shell cat .rpm_version)

BUILD_METADATA ?= "1~development~$(shell git rev-parse --short HEAD)"
RPM_SPEC_FILE ?= ${NAME}.spec
RPM_SOURCE_NAME ?= ${NAME}-${.FS_VERSION}
RPM_BUILD_DIR ?= $(PWD)/dist/rpmbuild
RPM_SOURCE_PATH := ${RPM_BUILD_DIR}/SOURCES/${RPM_SOURCE_NAME}.tar.bz2

build: rpm_package_source rpm_build_source rpm_build

prepare:
		rm -rf ${BUILD_DIR}
		mkdir -p ${BUILD_DIR}/SPECS ${BUILD_DIR}/SOURCES
		cp ${SPEC_FILE} ${BUILD_DIR}/SPECS/

rpm_package_source:
	tar --transform 'flags=r;s,^,/$(RPM_SOURCE_NAME)/,' --exclude .git --exclude dist -cvjf $(RPM_SOURCE_PATH) .

rpm_build_source:
	BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ts $(RPM_SOURCE_PATH) --define "_topdir $(RPM_BUILD_DIR)"

rpm_build:
	BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ba $(SPEC_FILE) --define "_topdir $(BUILD_DIR)"