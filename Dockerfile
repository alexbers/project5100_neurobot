FROM ubuntu:18.04

#RUN adduser neurobot -u 10000 --disabled-password
RUN useradd -u 10000 neurobot

RUN apt-get update
RUN apt-get install -y gcc
RUN apt-get install -y python3 python3-dev
RUN apt-get install -y python3-flask
RUN apt-get install -y python3-numpy
RUN apt-get install -y python3-pip

RUN pip3 install catboost
RUN pip3 install gunicorn

RUN true

COPY model /home/neurobot/model/
COPY start.sh game.py mcts.py neurobot_srv.py nnet.py /home/neurobot/

RUN chown -R neurobot:neurobot /home/neurobot

WORKDIR /home/neurobot/
CMD ["./start.sh"]
