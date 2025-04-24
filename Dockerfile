FROM ubuntu:latest
LABEL authors="Guzma"

ENTRYPOINT ["top", "-b"]