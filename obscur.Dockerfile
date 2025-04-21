FROM python:3.13-bookworm
USER root

ARG USER=tor-scraper
ENV HOME=/home/$USER

RUN apt-get update && \
  apt-get install -y \
  curl \
  libx11-xcb1 \
  libasound2 \
  libdbus-glib-1-2 \
  libgtk-3-0 \
  libxrender1 \
  libxt6 \
  xvfb \
  xz-utils && \
  rm -rf /var/lib/apt/lists/*

RUN useradd --uid 1000 --create-home --home-dir $HOME $USER && \
  mkdir -p $HOME/scraper && \
  chown -R $USER:$USER $HOME

USER 1000
WORKDIR $HOME

# Setup TBB
ENV TBB_PATH=$HOME/tor-browser
COPY scripts/install_tbb.sh .
RUN bash install_tbb.sh
COPY assets/stealth/profile.tar.xz /tmp/profile.tar.xz
RUN tar -xJf /tmp/profile.tar.xz -C $TBB_PATH/Browser/TorBrowser/Data/Browser

# Setup python
COPY src/requirements.txt .
RUN pip3 install -r requirements.txt

# Setup scraper
WORKDIR $HOME/tor-scraper
COPY src .

ENV CONFIG_FOLDER=$HOME/config
ENV RSS_FOLDER=$HOME/rss
ENV DATA_FOLDER=$HOME/data
ENV PYTHONUNBUFFERED=1

VOLUME [ "${CONFIG_FOLDER}", "${RSS_FOLDER}", "${DATA_FOLDER}", "${HOME}/nltk_data" ]

CMD [ "python3", "main.py" ]
