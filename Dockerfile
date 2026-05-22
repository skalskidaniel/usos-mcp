#TODO
FROM python3.11:slim
LABEL authors="Daniel Skalski"

ENTRYPOINT ["top", "-b"]