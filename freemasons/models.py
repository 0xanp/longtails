import datetime
import django
import requests

from django.conf import settings
from django.db import models

from .utils import needs_sync

# Designed to support docs/social/freemason-frontrunning.md
# Create FreeMasonProject
#       - From that time on Longtails will watch the follower records of
#         holders of that project
# Every 12 hours a clock runs to refresh the primary brand
#       members (alpha generators)

URLS = {
    "TOKEN_OWNER": "https://deep-index.moralis.io/api/v2/nft/{0}/{1}/owners?chain=eth&format=decimal",
    "MEMBER": "https://www.nftinspect.xyz/_next/data/{0}/profiles/{1}.json",
    "MEMBERS": "http://www.nftinspect.xyz/api/collections/members/{0}?limit=2000&onlyNewMembers=false"
}


class TwitterUser(models.Model):
    identifier = models.CharField(max_length=256, null=True)

    name = models.CharField(max_length=256, null=True)
    username = models.CharField(max_length=256)

    pfp_url = models.TextField(null=True)
    token = models.CharField(max_length=256, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FreeMasonMember(models.Model):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if needs_sync(self.last_sync_at):
            self.sync()

    twitter = models.ForeignKey(TwitterUser, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=256)

    followers = models.ManyToManyField(TwitterUser, related_name="followers")
    following = models.ManyToManyField(TwitterUser, related_name="following")

    last_sync_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_wallet(self):
        headers = {
            'accept': 'application/json',
            'X-API-KEY': settings.MORALIS_API_KEY
        }

        token_split = self.twitter.token.split(':')
        contract_address = token_split[1]
        token_id = token_split[2]

        response = requests.get(URLS["TOKEN_OWNER"].format(
            contract_address, token_id
        ), headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            return response_data['result'][0]['owner_of']

        return ""

    def sync(self):
        self.wallet_address = self.get_wallet()

        self.last_sync_at = django.utils.timezone.now()
        self.save()

        return {"status": 200}

    ordering = ['-updated_at']


class FreeMasonProject(models.Model):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if needs_sync(self.last_sync_at):
            self.sync()

    contract_address = models.CharField(max_length=256)
    members = models.ManyToManyField(FreeMasonMember)

    last_sync_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def sync(self):
        response = requests.get(URLS["MEMBERS"].format(self.contract_address))

        if response.status_code == 200:
            response_data = response.json()

            self.members.clear()
            for member in response_data['members']:
                member_twitter_obj, created = TwitterUser.objects.get_or_create(
                    identifier=member['id'],
                )

                member_twitter_obj.name = member['name']
                member_twitter_obj.username = member['username']
                member_twitter_obj.pfp_url = member['pfpUrl']
                member_twitter_obj.token = member['token']
                member_twitter_obj.save()

                member_obj, created = FreeMasonMember.objects.get_or_create(
                    twitter=member_twitter_obj,
                )

                self.members.add(member_obj)

            self.last_sync_at = django.utils.timezone.now()
            self.save()

            return {"status": 200}
        return {"status": 500}
