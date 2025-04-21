#!/usr/bin/env bash
set -xe
echo "Installing TorBrowser in $HOME/tor-browser"

if [ "$(arch)" == "aarch64" ]; then
  SF_VERSION=$(curl -sI https://sourceforge.net/projects/tor-browser-ports/files/latest/download | awk -F'(ports/|/tor)' '/location/ {print $3}')
  FULL_TOR_URL="https://downloads.sourceforge.net/project/tor-browser-ports/${SF_VERSION}/tor-browser-linux-arm64-${SF_VERSION}.tar.xz"
else
  TOR_URL=$(curl -sq https://www.torproject.org/download/ | grep downloadLink | grep linux | sed 's/.*href="//g'  | cut -d '"' -f1 | head -1)
  FULL_TOR_URL="https://www.torproject.org/${TOR_URL}"
fi
curl -L "${FULL_TOR_URL}" -o /tmp/torbrowser.tar.xz
tar -xJf /tmp/torbrowser.tar.xz -C $HOME
rm /tmp/torbrowser.tar.xz

echo "Installation done"
echo "Set your TBB_PATH environment variable to $HOME/tor-browser"
