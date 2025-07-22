# ============= LLM Output Processing =============
"""
Output processors for cleaning and structuring LLM responses.
"""

import re
from typing import List


class OutputProcessors:
    """Functions to process and clean LLM outputs"""

    @staticmethod
    def clean_all_llm_responses(raw_response: str) -> str:
        """Universal LLM response cleaner that preserves Markdown formatting"""
        if not raw_response or not isinstance(raw_response, str):
            return ""

        # Remove reasoning patterns at the start while preserving structured content
        reasoning_start_patterns = [
            r"^.*?(?=\*\*Key Nutrients)",  # Remove everything before **Key Nutrients
            r"^.*?(?=🚨\s*\*\*EMERGENCY)",  # Remove everything before emergency alerts
            r"^.*?(?=📋\s*\*\*Your Complete Profile)",  # Remove everything before profile
            r"^.*?(?=🗓️\s*\*\*Your ANC Schedule)",  # Remove everything before schedule
            r"^.*?(?=\{)",  # Remove everything before JSON starts
        ]

        # Apply the first matching pattern
        cleaned_response = raw_response
        for pattern in reasoning_start_patterns:
            match = re.search(pattern, raw_response, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned_response = raw_response[match.end() :]
                break

        # Remove specific reasoning phrases while preserving line structure
        reasoning_patterns = [
            r"^.*?(?:let me start by|first,? let me|i'll start by).*?(?=\n|$)",
            r"^.*?(?:i need to|i should|i'll|let me).*?(?=\n\*\*|$)",
            r"^.*?(?:considering your|based on your|for you).*?(?=\n\*\*|$)",
            r"^.*?(?:personalized nutrition advice for week \d+|nutrition recommendations for).*?(?=\n\*\*|$)",
        ]

        lines = cleaned_response.split("\n")
        filtered_lines = []

        for line in lines:
            # Check if line is pure reasoning text
            is_reasoning = False
            for pattern in reasoning_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_reasoning = True
                    break

            # Skip reasoning lines but keep all structured content
            if not is_reasoning:
                filtered_lines.append(line)

        # Join lines back, preserving empty lines for formatting
        result = "\n".join(filtered_lines)

        # Clean up excessive empty lines but preserve single empty lines
        result = re.sub(r"\n\n\n+", "\n\n", result)

        return result.strip()

    @staticmethod
    def clean_nutrition_response(raw_response: str) -> str:
        """Clean nutrition response while preserving proper Markdown formatting"""
        if not raw_response or not isinstance(raw_response, str):
            return ""

        # First apply universal cleaning
        cleaned = OutputProcessors.clean_all_llm_responses(raw_response)

        # Split into lines and process to ensure proper Markdown structure
        lines = cleaned.split("\n")
        formatted_lines = []

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                # Preserve empty lines for spacing
                formatted_lines.append("")
                continue

            # Ensure headers have proper Markdown formatting and spacing
            if any(
                keyword in line.lower()
                for keyword in [
                    "key nutrients",
                    "daily meal",
                    "essential",
                    "foods to avoid",
                    "practical tips",
                ]
            ) and not line.startswith("**"):
                line = f"**{line.replace('**', '')}**"
                # Add spacing before major sections (except the first one)
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append("")

            # Add spacing before major section headers that are already formatted
            elif line.startswith("**") and any(
                keyword in line.lower()
                for keyword in ["essential", "foods to avoid", "practical tips"]
            ):
                # Add spacing before these sections if there's content above
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append("")

            # Ensure bullet points are properly formatted
            elif line and not line.startswith(("**", "- ", "•")) and i > 0:
                prev_line = lines[i - 1].strip() if i > 0 else ""
                # If previous line was a header and current line looks like content, make it a bullet
                if (
                    prev_line.startswith("**")
                    and ":" in line
                    and not any(
                        meal in line.lower()
                        for meal in ["breakfast", "lunch", "dinner"]
                    )
                ):
                    line = f"- {line}"

            formatted_lines.append(line)

        # Clean up excessive empty lines but preserve intentional spacing
        result = "\n".join(formatted_lines)
        result = re.sub(r"\n\n\n+", "\n\n", result)

        return result.strip()

    @staticmethod
    def enforce_nutrition_structure(content: str, week: int) -> str:
        """Enforce exact nutrition response structure"""
        if not content or not any(
            keyword in content.lower() for keyword in ["key nutrients", "meal plan"]
        ):
            # If response doesn't contain expected sections, return fallback structure
            return f"""**Key Nutrients for Week {week}:**
            - Folic acid: prevents birth defects
            - Iron: supports blood production
            - Calcium: builds strong bones
            - Protein: supports baby's growth

            **Daily Meal Plan:**
            **Breakfast:** Rice porridge with dal (1 bowl)
            **Mid-Morning:** Banana with yogurt (1 small cup)
            **Lunch:** Rice with fish curry and shak (1 plate)
            **Afternoon:** Boiled egg with crackers (1 egg, 2 crackers)
            **Dinner:** Dal with rice and vegetables (1 bowl each)
            **Before Bed:** Warm milk (1 glass)

            **Essential Bangladeshi Foods:**
            - Dal (lentils): high in protein and folate
            - Shak (leafy greens): rich in iron and vitamins
            - Hilsa fish: provides omega-3 fatty acids
            - Rice: main energy source
            - Seasonal fruits: vitamin C and fiber

            **Foods to Avoid:**
            - Raw fish: risk of infection
            - Unpasteurized dairy: bacterial contamination
            - Raw papaya: may cause contractions

            **Practical Tips:**
            - Eat small, frequent meals to manage nausea
            - Cook vegetables thoroughly for safety
            - Include variety of colors in meals
            - Stay hydrated with clean water"""

        return content
