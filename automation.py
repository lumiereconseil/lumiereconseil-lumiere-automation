import argparse
import os
import sys

REQUIRED_LIVE_SECRETS = [
    "ANTHROPIC_API_KEY",
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
    "IG_ACCESS_TOKEN",
    "IG_BUSINESS_ACCOUNT_ID",
    "YT_API_KEY",
]


def preflight() -> int:
    missing = [name for name in REQUIRED_LIVE_SECRETS if not os.getenv(name)]
    if missing:
        print("Preflight: missing live secrets: " + ", ".join(missing))
        return 2
    print("Preflight: required live secrets are configured.")
    return 0


def run_daily_automation() -> None:
    # Imports are delayed so CI validation can run without creating API clients.
    from libs.twitter_client import TwitterClient
    from libs.instagram_client import InstagramClient
    from libs.youtube_client import YouTubeClient
    from libs.content_generator import ContentGenerator
    from libs.metrics_logger import log_result

    if preflight() != 0:
        raise RuntimeError("Live automation blocked: required secrets are missing.")

    generator = ContentGenerator()
    twitter = TwitterClient()
    instagram = InstagramClient()
    youtube = YouTubeClient()

    topic = "Lumiere Conseil: practical AI productivity and side-business tips"
    content = generator.generate_post(topic)
    text = content["content"][0]["text"]

    tweet_res = twitter.post_tweet(text)
    insta_res = instagram.post_photo(
        image_url="https://picsum.photos/800",
        caption=text,
    )
    yt_res = youtube.search_video("AI productivity side business")

    # Stripe mutations were intentionally removed. Daily automation must never
    # create dummy customers or subscriptions.
    log_result({
        "tweet": tweet_res,
        "instagram": insta_res,
        "youtube": yt_res,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate configuration only")
    args = parser.parse_args()
    if args.check:
        sys.exit(preflight())
    run_daily_automation()
