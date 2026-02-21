[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Tsingis_telegram-bot&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Tsingis_telegram-bot)

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

- Install deps `npm install` in respective folder

- Deploy lambda with Serverless
  1. Set .env file / environment variables
  2. Start Docker
  3. Create requirements to deploy `pipenv requirements > serverless/requirements.txt`
  4. Deploy `npm run deploy`

- Deploy other resources with Pulumi
  1. Setup stacks `Pulumi.{stack-name}.yml`
  2. Select stack `pulumi stack select {stack-name}`
  3. Refresh `pulumi refresh`
  4. Deploy `pulumi up`
