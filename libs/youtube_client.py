import os
from googleapiclient.discovery import build

class YouTubeClient:
    def __init__(self):
        self.api_key = os.getenv("YT_API_KEY")
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def search_video(self, query: str):
        request = self.youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1
        )
        response = request.execute()
        return response

