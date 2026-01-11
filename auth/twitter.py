"""Get Twitter Access Token and Access Token Secret via OAuth 1.0a"""
import os
from requests_oauthlib import OAuth1Session

# Your API credentials
API_KEY = "mDyIwhsg9nzz3SI7QsJIXLsEE"
API_SECRET = "Er4XN1L2V2Zd0mun3Y5kJ94SY5HZWQEnaaChRTpVbIhkbTi8O3"

# Twitter OAuth endpoints
REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

def get_tokens():
    # Step 1: Get request token
    oauth = OAuth1Session(API_KEY, client_secret=API_SECRET, callback_uri="oob")

    try:
        fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    except Exception as e:
        print(f"Error getting request token: {e}")
        print("\nMake sure your Twitter App has 'Read and Write' permissions enabled.")
        print("Go to: https://developer.twitter.com/en/portal/projects-and-apps")
        print("→ Your App → Settings → User authentication settings → Edit")
        print("→ Set 'App permissions' to 'Read and write'")
        return

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")

    # Step 2: Get authorization URL
    authorization_url = oauth.authorization_url(AUTHORIZE_URL)

    print("\n" + "="*60)
    print("TWITTER AUTHORIZATION")
    print("="*60)
    print("\n1. Open this URL in your browser:\n")
    print(f"   {authorization_url}")
    print("\n2. Log in to Twitter and authorize the app")
    print("\n3. Twitter will show you a PIN code")
    print("\n" + "="*60)

    # Step 3: Get PIN from user
    verifier = input("\nEnter the PIN code from Twitter: ").strip()

    # Step 4: Get access token
    oauth = OAuth1Session(
        API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )

    try:
        oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    except Exception as e:
        print(f"\nError getting access token: {e}")
        return

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    print("\n" + "="*60)
    print("SUCCESS! Here are your tokens:")
    print("="*60)
    print(f"\nTWITTER_ACCESS_TOKEN={access_token}")
    print(f"TWITTER_ACCESS_TOKEN_SECRET={access_token_secret}")
    print("\n" + "="*60)
    print("\nAdd these to your .env file, then tweets will work!")
    print("="*60)

    # Optionally update .env automatically
    update = input("\nUpdate .env automatically? (y/n): ").strip().lower()
    if update == 'y':
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        with open(env_path, 'r') as f:
            content = f.read()

        content = content.replace('TWITTER_ACCESS_TOKEN=', f'TWITTER_ACCESS_TOKEN={access_token}')
        content = content.replace('TWITTER_ACCESS_TOKEN_SECRET=', f'TWITTER_ACCESS_TOKEN_SECRET={access_token_secret}')

        with open(env_path, 'w') as f:
            f.write(content)

        print("\n✓ .env updated successfully!")

if __name__ == "__main__":
    get_tokens()
