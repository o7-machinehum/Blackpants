FROM kicad/kicad:9.0

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install make, pip, and kikit for hardware build pipeline
USER root
RUN mkdir -p /var/lib/apt/lists/partial && \
    apt-get update && \
    apt-get install -y --no-install-recommends make python3-pip && \
    python3 -m pip install --break-system-packages kikit && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Switch back to kicad user for security
USER kicad

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
