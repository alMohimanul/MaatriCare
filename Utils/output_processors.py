import re
from typing import List


class OutputProcessors:
    """Functions to process and clean LLM outputs"""

    @staticmethod
    def clean_all_llm_responses(raw_response: str) -> str:
        """Universal LLM response cleaner that removes thinking/reasoning and preserves Markdown formatting"""
        if not raw_response or not isinstance(raw_response, str):
            return ""

        # STEP 1: Remove any <think> tags and their content completely (most aggressive)
        cleaned_response = re.sub(
            r"<think>.*?</think>", "", raw_response, flags=re.DOTALL | re.IGNORECASE
        )

        # STEP 2: Remove any thinking blocks that might not have proper tags
        cleaned_response = re.sub(
            r"<think[^>]*>.*?</think[^>]*>",
            "",
            cleaned_response,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # STEP 3: Remove standalone thinking sections with various formats
        thinking_section_patterns = [
            r"\*\*Thinking and Reasoning\*\*.*?(?=\n\*\*|\n\n|\Z)",
            r"\*\*Thinking\*\*.*?(?=\n\*\*|\n\n|\Z)",
            r"\*\*Reasoning\*\*.*?(?=\n\*\*|\n\n|\Z)",
            r"##\s*Thinking.*?(?=\n##|\n\n|\Z)",
            r"###\s*Thinking.*?(?=\n###|\n\n|\Z)",
        ]

        for pattern in thinking_section_patterns:
            cleaned_response = re.sub(
                pattern, "", cleaned_response, flags=re.DOTALL | re.IGNORECASE
            )

        # STEP 4: Remove instruction lines about thinking
        instruction_patterns = [
            r"- Use <think> tag for thinking steps\.?\s*",
            r"Use <think> tag for thinking steps\.?\s*",
            r".*?<think>.*?thinking steps.*?\n?",
            r".*?thinking.*?steps.*?\n?",
        ]

        for pattern in instruction_patterns:
            cleaned_response = re.sub(
                pattern, "", cleaned_response, flags=re.IGNORECASE
            )

        # Remove thinking/reasoning patterns at the start
        reasoning_start_patterns = [
            r"^.*?(?=\*\*.*?:)",  # Remove everything before **Header:
            r"^.*?(?=🚨\s*\*\*EMERGENCY)",  # Remove everything before emergency alerts
            r"^.*?(?=📋\s*\*\*Your Complete Profile)",  # Remove everything before profile
            r"^.*?(?=🗓️\s*\*\*Your ANC Schedule)",  # Remove everything before schedule
            r"^.*?(?=\{)",  # Remove everything before JSON starts
            r"^.*?(?=I understand|I can hear|Looking at|Based on|For your|During)",  # Remove reasoning intro
        ]

        for pattern in reasoning_start_patterns:
            match = re.search(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned_response = cleaned_response[match.end() :]
                break

        # Remove specific reasoning phrases while preserving line structure
        reasoning_patterns = [
            r"^.*?(?:let me start by|first,? let me|i'll start by|let me provide|i'll help you).*?(?=\n|$)",
            r"^.*?(?:i need to|i should|i'll|let me).*?(?=\n\*\*|$)",
            r"^.*?(?:considering your|based on your|for you,|looking at your).*?(?=\n\*\*|$)",
            r"^.*?(?:personalized.*?advice|recommendations for|guidance for).*?(?=\n\*\*|$)",
            r"^.*?(?:here's|here are|this is|these are).*?(?=\n\*\*|$)",
            r"^.*?(?:during this|in this|at this stage|for this trimester).*?(?=\n\*\*|$)",
        ]

        lines = cleaned_response.split("\n")
        filtered_lines = []

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                filtered_lines.append(line)
                continue

            is_reasoning = False

            if not any(
                marker in line_stripped
                for marker in ["**", "•", "-", "🚨", "📋", "🗓️", "🎯", "⚠️", "✅"]
            ):
                for pattern in reasoning_patterns:
                    if re.match(pattern, line_stripped, re.IGNORECASE):
                        is_reasoning = True
                        break

                reasoning_keywords = [
                    "let me",
                    "i understand",
                    "i can see",
                    "looking at",
                    "based on your",
                    "for your current",
                    "during this stage",
                    "at this point",
                    "considering",
                    "i'll provide",
                    "here's what",
                    "this will help",
                    "i need to",
                    "i should",
                    "first, let me",
                    "let me think",
                    "thinking about",
                    "i'll analyze",
                    "analyzing",
                    "i notice",
                    "i see that",
                    "given that",
                    "since you",
                    "i'll focus",
                    "focusing on",
                    "let me address",
                    "addressing your",
                    "taking into account",
                    "considering that",
                    "i'll start",
                    "starting with",
                ]

                if (
                    any(
                        keyword in line_stripped.lower()
                        for keyword in reasoning_keywords
                    )
                    and len(line_stripped) < 150
                    and not any(
                        marker in line_stripped
                        for marker in ["**", "•", "-", "🚨", "📋", "🗓️", "🎯", "⚠️", "✅"]
                    )
                ):
                    is_reasoning = True

                thinking_patterns = [
                    r"^(let me|i\'ll|i need to|i should|considering|based on|looking at|given that|since you|taking into account)",
                    r"(think about|analyze|focus on|address|start with)",
                ]

                for pattern in thinking_patterns:
                    if re.match(pattern, line_stripped.lower()) and not any(
                        marker in line_stripped for marker in ["**", "•", "-"]
                    ):
                        is_reasoning = True
                        break

            if not is_reasoning:
                filtered_lines.append(line)

        result = "\n".join(filtered_lines)

        result = re.sub(r"\n\n\n+", "\n\n", result)

        # Remove any remaining reasoning fragments at the start
        result = re.sub(
            r"^[^*•\-🚨📋🗓️]*?(?=\*\*|\n\*\*)", "", result, flags=re.MULTILINE
        )

        # FINAL CLEANUP: Remove any remaining thinking-related content (AGGRESSIVE)
        final_cleanup_patterns = [
            r".*?<think>.*?</think>.*?\n?",  # Any remaining think tags
            r".*thinking.*steps.*\n?",  # Any remaining thinking instructions
            r"^.*reasoning.*\n?",  # Any reasoning lines
            r"^.*analysis.*\n?",  # Any analysis lines that aren't structured
            r".*use.*think.*tag.*\n?",  # Any remaining think tag instructions
            r".*<think.*?>.*\n?",  # Any malformed think tags
            r".*</think.*?>.*\n?",  # Any malformed think closing tags
            r"^thinking.*\n?",  # Lines starting with "thinking"
            r"^reasoning.*\n?",  # Lines starting with "reasoning"
            r".*\bthink\b.*steps.*\n?",  # Any mention of think + steps
            r".*\breason\b.*steps.*\n?",  # Any mention of reason + steps
        ]

        for pattern in final_cleanup_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)

        # Remove any lines that are purely instructional about thinking
        lines = result.split("\n")
        final_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            # Skip lines that are purely about thinking/reasoning instructions
            if not (
                (
                    "think" in line_lower
                    and ("tag" in line_lower or "step" in line_lower)
                )
                or ("reasoning" in line_lower and len(line_lower) < 50)
                or (
                    "analysis" in line_lower
                    and len(line_lower) < 50
                    and not line_lower.startswith("**")
                )
                or line_lower.startswith("thinking")
                or line_lower.startswith("reasoning")
            ):
                final_lines.append(line)

        result = "\n".join(final_lines)

        result = re.sub(r"\n\n\n+", "\n\n", result)

        return result.strip()

    @staticmethod
    def clean_nutrition_response(raw_response: str) -> str:
        """Clean nutrition response while preserving proper Markdown formatting"""
        if not raw_response or not isinstance(raw_response, str):
            return ""

        cleaned = OutputProcessors.clean_all_llm_responses(raw_response)

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
