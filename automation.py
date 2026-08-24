from libs.twitter_client import TwitterClient
from libs.instagram_client import InstagramClient
from libs.youtube_client import YouTubeClient
from libs.stripe_client import StripeClient
from libs.content_generator import ContentGenerator
from libs.metrics_logger import log_result

def run_daily_automation():
    generator = ContentGenerator()
    twitter = TwitterClient()
    instagram = InstagramClient()
    youtube = YouTubeClient()
    stripe = StripeClient()

    # 1. Generate content
    topic = "Latest trends in global HR and leadership"
    content = generator.generate_post(topic)

    # 2. Post to Twitter
    tweet_res = twitter.post_tweet(content["content"][0]["text"])

    # 3. Post to Instagram
    insta_res = instagram.post_photo(
        image_url="https://picsum.photos/800",
        caption=content["content"][0]["text"]
    )

    # 4. YouTube search (example)
    yt_res = youtube.search_video("HR leadership trends")

    # 5. Stripe example (dummy)
    customer = stripe.create_customer("example@example.com")

    # 6. Log results
    log_result({
        "tweet": tweet_res,
        "instagram": insta_res,
        "youtube": yt_res,
        "stripe": customer
    })

if __name__ == "__main__":
    run_daily_automation()

