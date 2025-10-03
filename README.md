[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Tsingis_telegram-bot&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Tsingis_telegram-bot) [![Deploy Status](https://github.com/tsingis/telegram-bot/actions/workflows/lambda.yml/badge.svg)](https://github.com/tsingis/telegram-bot/actions/workflows/lambda.yml)

# Telegram bot running on AWS Lambda that uses APIs or scraped data

## Current features:

**F1**

- Upcoming race
- Standings (both driver and team)
- Latest race results

**NHL** (partially lost features due to completely new API)

- NHL regular season scoring leaders (by team or nationality)
- NHL player contract (by name)

**Other**

- Weather info (by location)
- Random picture (by keyword)

## How it works:

![alt text](https://i.imgur.com/KSxMkXk.png)

## Tools

- Python
- Docker
- AWS
- Node.js
- Serverless Framework
- Pulumi

## Dev environment setup

- Install pipenv globally `pip install -r requirements.txt`
- Set up environment `pipenv install --ignore-pipfile --dev`
- Activate virtual environment `pipenv shell`

## Manual deployment

- Install deps `npm install`

- Deploy lambda with Serverless
  1. Start Docker
  2. Activate virtual environment if not active `pipenv shell`
  3. Deploy `npm run deploy`

- Deploy other resources with Pulumi
  1. Setup stacks `Pulumi.{stack-name}.yml`
  2. Select stack `pulumi stack select {stack-name}`
  3. Refresh `pulumi refresh`
  4. Deploy `pulumi up`
