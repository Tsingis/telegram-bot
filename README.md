# Telegram bot running on AWS Lambda that uses APIs or scraped data

## Current features:

**F1**

- Upcoming race
- Standings (both driver and team)
- Latest race results

**NHL**

- Upcoming matches
- Regular season standings
- Latest match results
- Regular season scoring leaders (with given amount and or nationality)
- Players' basic stats from the latest matches (by nationality or team)
- Player's regular season stats (by name)
- Playoffs bracket

**Other**

- Weather info (by location)
- Random picture (by keyword)

## How it works:

![alt text](https://i.imgur.com/j4oKHUa.png)

## Requirements:

- AWS Account
- Python 3.11
- Node.js 18.x
- Serverless Framework
- Docker Desktop

## Manual deployment

1. Set environment variables
2. Start Docker Desktop
3. Run `npm install`
4. Run `serverless deploy --aws-profile PROFILE`
