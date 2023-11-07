# Telegram bot running on AWS Lambda that uses APIs or scraped data

## Current features:

**F1**

- Upcoming race
- Standings (both driver and team)
- Latest race results

**NHL** (disabled due to completely new API)

**Other**

- Weather info (by location)
- Random picture (by keyword)

## How it works:

![alt text](https://i.imgur.com/j4oKHUa.png)

## Requirements:

- AWS Account
- Python 3.11
- Node.js 20
- Serverless Framework
- Docker Desktop

## Manual deployment

1. Set environment variables
2. Start Docker Desktop
3. Run `npm install`
4. Run `serverless deploy --aws-profile PROFILE`
