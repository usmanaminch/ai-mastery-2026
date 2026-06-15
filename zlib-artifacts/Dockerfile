# Security Research Environment
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    llvm \
    git \
    cmake \
    python3 \
    wget \
    curl \
    vim \
    gdb \
    pkg-config \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# Install AFL++
RUN apt-get update && apt-get install -y afl++ || \
    (git clone https://github.com/AFLplusplus/AFLplusplus && cd AFLplusplus && make distrib && make install)

# Set up environment variables
ENV CC=clang
ENV CXX=clang++

WORKDIR /workspace

CMD ["/bin/bash"]
