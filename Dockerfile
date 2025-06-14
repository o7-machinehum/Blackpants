# This file contains the base image for CI builds of this project.
# Its purpose is to provide a minimal environment with the necessary tools to export PCB designs / fab files.
# Image is stored in Gitlab Container Registry at registry.gitlab.com/why2025/team-badge/hardware
# Lookup: https://gitlab.com/why2025/team-badge/Hardware/container_registry
FROM alpine:latest

# Kicad+Kikit layer
RUN apk update && apk add py3-kikit --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/

# Other dependencies (wx needed for kikit fabrication export)
RUN apk add make py3-wxpython
