#!/bin/bash

PROJECT_PATH="${PROJECT_PATH:=/opt/star-burger/}"

set -e

cd $PROJECT_PATH

repo_update_result=$(git pull)

if [[ $repo_update_result="Already up to date." ]]
then
  echo $repo_update_result
  exit
fi

./venv/bin/pip install -r requirements.txt --no-input
./venv/bin/python manage.py migrate --no-input
./venv/bin/python manage.py collectstatic --no-input

npm ci
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

systemctl restart star_burger.service

echo "Deployment successfully completed"
