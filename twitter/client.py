import asyncio
import requests

from django.conf import settings

USER_HEAD = "https://api.twitter.com/2/users/"
TWEETS_HEAD = "https://api.twitter.com/2/tweets/"

URLS = {
    "USERNAME_TO_ID": USER_HEAD + "by/username/{0}",
    "USERNAMES_TO_ID": USER_HEAD + "by?usernames={0}",
    "FOLLOWERS": USER_HEAD + "{0}/followers",
    "FOLLOWING": USER_HEAD + "{0}/following",
    "LIKES": USER_HEAD + "{0}/liked_tweets",
    "RETWEETS": TWEETS_HEAD + "{0}/retweeted_by"
}


class TwitterClient:
    """
    Client that enables the ability to interface with the Twitter API with ease.

    Must have acecss to the Twitter API.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.headers = {
            'Authorization': f'Bearer {settings.TWITTER_BEARER_TOKEN}',
        }

    def handle_request(self, url):
        return requests.get(
            url,
            headers=self.headers
        )

    async def handle_response(self, response):
        print('[Twitter Client] [Pausing] 30 Seconds.')
        await asyncio.sleep(30)

        if response.status_code == 200:
            if 'data' in response.json():
                return response.json()['data']
            return []

        print('[Twitter Client] [Error]', response.json())
        return {} 

    async def get_username_ids(self, usernames):
        response = self.handle_request(
            URLS["USERNAMES_TO_ID"].format(','.join(usernames)))
        return await self.handle_response(response)

    async def get_followers(self, user_id):
        response = self.handle_request(URLS["FOLLOWERS"].format(user_id))
        return await self.handle_response(response)

    async def get_following(self, user_id):
        response = self.handle_request(URLS["FOLLOWING"].format(user_id))
        return await self.handle_response(response)

    async def get_likes(self, user_id):
        response = self.handle_request(URLS["LIKES"].format(user_id))
        return await self.handle_response(response)

    async def get_retweets(self, user_id):
        response = self.handle_request(URLS["RETWEETS"].format(user_id))
        return await self.handle_response(response)
