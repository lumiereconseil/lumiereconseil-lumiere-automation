import argparse
import json
import os
import sys

X_REQUIRED_SECRETS = [
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
]


def preflight() -> int:
    required = ["ANTHROPIC_API_KEY", *X_REQUIRED_SECRETS]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("Preflight: missing credentials: " + ", ".join(missing))
        return 2
    print("Preflight: content generation and X credentials are configured.")
    return 0


def run_daily_automation() -> None:
    # Each channel is handled independently. Missing credentials must not
    # block status logging for the whole run, and no unapproved media is posted.
    from libs.metrics_logger import log_result

    results = {}
    api_key = os.getenv("ANTHROPIC_API_KEY")
    x_missing = [name for name in X_REQUIRED_SECRETS if not os.getenv(name)]

    generated_text = None
    if not api_key:
        results["content_generation"] = {
            "status": "skipped",
            "reason": "missing ANTHROPIC_API_KEY",
        }
    else:
        try:
            from libs.content_generator import ContentGenerator

            response = ContentGenerator().generate_post(
                "Lumiere Conseil: practical AI productivity and side-business tips"
            )
            if not isinstance(response, dict) or "content" not in response:
                raise RuntimeError("Content API returned no content field")
            generated_text = response["content"][0]["text"].strip()
            if not generated_text:
                raise RuntimeError("Content API returned empty text")
            results["content_generation"] = {"status": "success"}
        except Exception as exc:
            results["content_generation"] = {
                "status": "failed",
                "reason": str(exc)[:300],
            }

    if x_missing:
        results["x"] = {
            "status": "skipped",
            "reason": "missing credentials: " + ", ".join(x_missing),
        }
    elif not generated_text:
        results["x"] = {
            "status": "skipped",
            "reason": "content generation did not succeed",
        }
    else:
        try:
            from libs.twitter_client import TwitterClient

            results["x"] = {
                "status": "success",
                "response": TwitterClient().post_tweet(generated_text),
            }
        except Exception as exc:
            results["x"] = {"status": "failed", "reason": str(exc)[:300]}

    # Instagram publishing is intentionally skipped until an owner-approved
    # branded image and a complete credential set are configured. The former
    # random-image URL is not suitable for unattended commercial publishing.
    results["instagram"] = {
        "status": "skipped",
        "reason": "requires owner-approved media asset and verified credentials",
    }

    # YouTube search does not publish content; do not report it as a publishing
    # action. Add a separate, explicitly reviewed workflow if publishing is needed.
    results["youtube"] = {
        "status": "skipped",
        "reason": "search-only API call is not a publishing action",
    }

    log_result(results)
    print(json.dumps(results, ensure_ascii=False, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate configuration only")
    args = parser.parse_args()
    if args.check:
        sys.exit(preflight())
    run_daily_automation()
