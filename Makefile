#
# MIT License
#
# (C) Copyright 2025 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

SHELL=/usr/bin/env bash -euo pipefail
NAME ?= license-checker
VERSION ?= $(shell git describe --tags)
PLATFORM ?= linux/amd64
REGISTRY ?= us-docker.pkg.dev/csm-release/csm-docker/unstable
DOCKER_BUILD_ARGS ?=
LOCAL ?= 1

.PHONY: local
local: image

.PHONY: unstable
unstable: LOCAL=
unstable: PLATFORM=linux/amd64,linux/arm64
unstable: image

.PHONY: stable
stable: LOCAL=
stable: PLATFORM=linux/amd64,linux/arm64
stable: REGISTRY=us-docker.pkg.dev/csm-release/csm-docker/stable
stable: image

.PHONY: image
image:
	docker buildx build $(if $(LOCAL),--load,--push) --platform $(PLATFORM) $(DOCKER_BUILD_ARGS) --tag $(REGISTRY)/$(NAME):$(VERSION) .
