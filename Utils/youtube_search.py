"""
YouTube Search Utility for MaatriCare

This module provides YouTube video search functionality for mood support and exercise content.
"""

import random
from typing import List, Dict, Any, Optional
from youtubesearchpython import VideosSearch
from Utils.constants import YouTubeConfig
from Utils.logging_config import get_logger

logger = get_logger(__name__)


class YouTubeSearchService:
    """Service for searching and curating YouTube videos for maternal health support"""

    def __init__(self):
        self.max_results = YouTubeConfig.MAX_RESULTS

    def search_mood_support_videos(self) -> List[Dict[str, str]]:
        """Search for mood support and emotional wellness videos"""
        try:
            # Randomly select a search query to get variety
            query = random.choice(YouTubeConfig.MOOD_SUPPORT_QUERIES)
            logger.info(f"Searching mood support videos with query: {query}")

            # Try to search with error handling for proxy issues
            try:
                videos_search = VideosSearch(query, limit=self.max_results)
                results = videos_search.result()
            except (TypeError, Exception) as e:
                error_msg = str(e).lower()
                if (
                    "proxies" in error_msg
                    or "proxy" in error_msg
                    or "unexpected keyword argument" in error_msg
                ):
                    logger.warning(f"YouTube search library compatibility error: {e}")
                    logger.info(
                        "Using fallback videos due to library compatibility issue"
                    )
                    return self._get_fallback_mood_videos()
                else:
                    logger.error(f"Unexpected error in YouTube search: {e}")
                    return self._get_fallback_mood_videos()

            if not results or "result" not in results:
                logger.warning("No mood support videos found")
                return self._get_fallback_mood_videos()

            curated_videos = []
            for video in results["result"][: self.max_results]:
                if self._is_appropriate_mood_video(video):
                    curated_videos.append(
                        {
                            "title": video.get("title", "Pregnancy Relaxation Video"),
                            "url": video.get("link", ""),
                            "duration": video.get("duration", "N/A"),
                            "description": self._generate_mood_description(
                                video.get("title", "")
                            ),
                        }
                    )

            if not curated_videos:
                return self._get_fallback_mood_videos()

            logger.info(f"Found {len(curated_videos)} mood support videos")
            return curated_videos

        except Exception as e:
            error_msg = str(e).lower()
            if (
                "proxies" in error_msg
                or "proxy" in error_msg
                or "unexpected keyword argument" in error_msg
            ):
                logger.warning(f"YouTube search library compatibility error: {e}")
                logger.info("Using fallback videos due to library compatibility issue")
            else:
                logger.error(f"Error searching mood support videos: {e}")
            return self._get_fallback_mood_videos()

    def search_exercise_videos(
        self, trimester: int, current_week: int = 0
    ) -> List[Dict[str, str]]:
        """Search for pregnancy exercise videos based on trimester"""
        try:
            # Get queries for the specific trimester
            if trimester not in YouTubeConfig.EXERCISE_QUERIES:
                trimester = 2  # Default to second trimester

            query = random.choice(YouTubeConfig.EXERCISE_QUERIES[trimester])
            logger.info(
                f"Searching exercise videos for trimester {trimester} with query: {query}"
            )

            # Try to search with error handling for proxy issues
            try:
                videos_search = VideosSearch(query, limit=self.max_results)
                results = videos_search.result()
            except (TypeError, Exception) as e:
                error_msg = str(e).lower()
                if (
                    "proxies" in error_msg
                    or "proxy" in error_msg
                    or "unexpected keyword argument" in error_msg
                ):
                    logger.warning(f"YouTube search library compatibility error: {e}")
                    logger.info(
                        "Using fallback exercise videos due to library compatibility issue"
                    )
                    return self._get_fallback_exercise_videos(trimester)
                else:
                    logger.error(f"Unexpected error in YouTube search: {e}")
                    return self._get_fallback_exercise_videos(trimester)

            if not results or "result" not in results:
                logger.warning(f"No exercise videos found for trimester {trimester}")
                return self._get_fallback_exercise_videos(trimester)

            curated_videos = []
            for video in results["result"][: self.max_results]:
                if self._is_appropriate_exercise_video(video):
                    curated_videos.append(
                        {
                            "title": video.get("title", "Prenatal Exercise Video"),
                            "url": video.get("link", ""),
                            "duration": video.get("duration", "N/A"),
                            "description": self._generate_exercise_description(
                                video.get("title", ""), trimester
                            ),
                        }
                    )

            if not curated_videos:
                return self._get_fallback_exercise_videos(trimester)

            logger.info(
                f"Found {len(curated_videos)} exercise videos for trimester {trimester}"
            )
            return curated_videos

        except Exception as e:
            error_msg = str(e).lower()
            if (
                "proxies" in error_msg
                or "proxy" in error_msg
                or "unexpected keyword argument" in error_msg
            ):
                logger.warning(f"YouTube search library compatibility error: {e}")
                logger.info(
                    "Using fallback exercise videos due to library compatibility issue"
                )
            else:
                logger.error(f"Error searching exercise videos: {e}")
            return self._get_fallback_exercise_videos(trimester)

    def _is_appropriate_mood_video(self, video: Dict[str, Any]) -> bool:
        """Check if video is appropriate for mood support"""
        title = video.get("title", "").lower()

        # Positive keywords
        positive_keywords = [
            "relaxation",
            "meditation",
            "calming",
            "positive",
            "affirmation",
            "pregnancy",
            "prenatal",
            "mindfulness",
            "peaceful",
            "soothing",
        ]

        # Negative keywords to avoid
        negative_keywords = [
            "labor",
            "birth",
            "delivery",
            "pain",
            "contractions",
            "scary",
            "dangerous",
            "risk",
            "complication",
            "problem",
        ]

        has_positive = any(keyword in title for keyword in positive_keywords)
        has_negative = any(keyword in title for keyword in negative_keywords)

        return has_positive and not has_negative

    def _is_appropriate_exercise_video(self, video: Dict[str, Any]) -> bool:
        """Check if video is appropriate for pregnancy exercise"""
        title = video.get("title", "").lower()

        # Positive keywords
        positive_keywords = [
            "pregnancy",
            "prenatal",
            "safe",
            "gentle",
            "yoga",
            "stretch",
            "exercise",
            "workout",
            "fitness",
            "trimester",
        ]

        # Negative keywords to avoid
        negative_keywords = [
            "intense",
            "extreme",
            "advanced",
            "hardcore",
            "dangerous",
            "weight loss",
            "diet",
            "abs workout",
            "core workout",
        ]

        has_positive = any(keyword in title for keyword in positive_keywords)
        has_negative = any(keyword in title for keyword in negative_keywords)

        return has_positive and not has_negative

    def _generate_mood_description(self, title: str) -> str:
        """Generate a helpful description for mood support videos"""
        title_lower = title.lower()

        if "meditation" in title_lower:
            return "A guided meditation to help you relax and find inner peace"
        elif "affirmation" in title_lower:
            return "Positive affirmations to boost your confidence and mood"
        elif "music" in title_lower or "calming" in title_lower:
            return "Soothing music to help you unwind and feel more peaceful"
        elif "yoga" in title_lower:
            return "Gentle yoga practice to reduce stress and anxiety"
        else:
            return "A supportive video to help improve your emotional wellbeing"

    def _generate_exercise_description(self, title: str, trimester: int) -> str:
        """Generate a helpful description for exercise videos"""
        title_lower = title.lower()

        trimester_text = f"trimester {trimester}"

        if "yoga" in title_lower:
            return f"Safe prenatal yoga exercises perfect for {trimester_text}"
        elif "stretch" in title_lower:
            return f"Gentle stretching routine suitable for {trimester_text}"
        elif "workout" in title_lower:
            return f"Low-impact workout designed for {trimester_text}"
        elif "back" in title_lower:
            return f"Exercises to relieve back pain during {trimester_text}"
        else:
            return f"Safe pregnancy exercises appropriate for {trimester_text}"

    def _get_fallback_mood_videos(self) -> List[Dict[str, str]]:
        """Provide fallback mood support videos when search fails"""
        return [
            {
                "title": "10-Minute Pregnancy Meditation",
                "url": "https://www.youtube.com/watch?v=5-s7ol7_6rA",
                "duration": "10:00",
                "description": "A calming guided meditation designed specifically for pregnant mothers",
            },
            {
                "title": "Positive Pregnancy Affirmations",
                "url": "https://www.youtube.com/watch?v=K9LTSB-Hf3w",
                "duration": "15:00",
                "description": "Daily affirmations to boost confidence and reduce anxiety during pregnancy",
            },
            {
                "title": "Relaxing Music for Pregnancy",
                "url": "https://www.youtube.com/watch?v=_vQIgmFZ4I0",
                "duration": "30:00",
                "description": "Peaceful instrumental music perfect for relaxation and stress relief",
            },
        ]

    def _get_fallback_exercise_videos(self, trimester: int) -> List[Dict[str, str]]:
        """Provide fallback exercise videos when search fails"""
        # Different videos based on trimester
        if trimester == 1:
            return [
                {
                    "title": "First Trimester Prenatal Yoga",
                    "url": "https://www.youtube.com/watch?v=CMbdULKjEg4",
                    "duration": "20:00",
                    "description": "Gentle yoga flows perfect for early pregnancy",
                },
                {
                    "title": "Safe First Trimester Exercises",
                    "url": "https://www.youtube.com/watch?v=YGkXpCaDu_c",
                    "duration": "15:00",
                    "description": "Low-impact exercises safe for weeks 1-12",
                },
                {
                    "title": "Pregnancy Stretches - First Trimester",
                    "url": "https://www.youtube.com/watch?v=QFCCOfWJpqk",
                    "duration": "12:00",
                    "description": "Gentle stretching routine for early pregnancy discomforts",
                },
            ]
        elif trimester == 2:
            return [
                {
                    "title": "Second Trimester Prenatal Yoga",
                    "url": "https://www.youtube.com/watch?v=nRzrWs7HEvo",
                    "duration": "25:00",
                    "description": "Energizing yoga practice for the second trimester",
                },
                {
                    "title": "Prenatal Pilates - Second Trimester",
                    "url": "https://www.youtube.com/watch?v=OZh3pNY4vBs",
                    "duration": "30:00",
                    "description": "Safe pilates exercises to maintain strength and flexibility",
                },
                {
                    "title": "Walking Workout for Pregnancy",
                    "url": "https://www.youtube.com/watch?v=iUzg9UNqHHs",
                    "duration": "20:00",
                    "description": "Indoor walking workout perfect for second trimester",
                },
            ]
        else:  # Third trimester
            return [
                {
                    "title": "Third Trimester Gentle Yoga",
                    "url": "https://www.youtube.com/watch?v=DjKXi6kEOrU",
                    "duration": "30:00",
                    "description": "Restorative yoga for late pregnancy comfort",
                },
                {
                    "title": "Labor Preparation Exercises",
                    "url": "https://www.youtube.com/watch?v=xFibaUGXhg0",
                    "duration": "15:00",
                    "description": "Gentle exercises to prepare your body for labor",
                },
                {
                    "title": "Prenatal Stretches for Back Pain",
                    "url": "https://www.youtube.com/watch?v=cC4MKm4gG0w",
                    "duration": "10:00",
                    "description": "Targeted stretches to relieve back pain in late pregnancy",
                },
            ]

    def format_videos_for_llm(self, videos: List[Dict[str, str]]) -> str:
        """Format video list for inclusion in LLM prompt"""
        if not videos:
            return "No videos available at this time."

        formatted_videos = []
        for i, video in enumerate(videos, 1):
            # Format links properly for UI conversion
            formatted_videos.append(
                f"{i}. [{video['title']}]({video['url']}): {video['description']}"
            )

        return "\n\n".join(formatted_videos)


# Global instance for easy access
youtube_service = YouTubeSearchService()
