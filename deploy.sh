#!/bin/bash

PROJECT_PATH="${PROJECT_PATH:=/opt/star-burger/}"

set -e

cd $PROJECT_PATH

source .env

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

last_commit_hash=$(git rev-parse --short HEAD)

# jo is a handy utility for creating json objects. See more details: https://github.com/jpmens/jo
rollbar_data=$(jo \
  environment=$PROFILE \
  revision=$last_commit_hash \
  rollbar_name=$ROLLBAR_NAME \
  local_username=$USER \
  comment="Deployment $last_commit_hash" \
  status=succeeded \
)

curl -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST 'https://api.rollbar.com/api/1/deploy' \
     -d "$rollbar_data" \
     -s > /dev/null

echo "Deployment successfully completed"
