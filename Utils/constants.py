import json
import re
from typing import List, Dict, Tuple, Any


class IntentKeywords:
    """Keywords for classifying user intents"""

    # Emergency keywords - highest priority
    EMERGENCY_KEYWORDS: List[str] = [
        "emergency",
        "urgent",
        "help",
        "bleeding heavily",
        "severe pain",
        "can't breathe",
        "chest pain",
        "dizzy",
        "faint",
        "contractions",
        "water broke",
        "baby not moving",
        "high blood pressure",
        "severe headache",
        "vision problems",
        "911",
        "999",
        "hospital",
    ]

    # Emergency type classification
    BLEEDING_KEYWORDS: List[str] = ["bleed", "blood"]
    PAIN_KEYWORDS: List[str] = ["pain", "hurt", "ache"]
    BREATHING_KEYWORDS: List[str] = ["breath", "chest", "air"]
    PRESSURE_KEYWORDS: List[str] = ["pressure", "headache", "vision"]

    # Regular intent keywords
    SCHEDULING_KEYWORDS: List[str] = ["appointment", "schedule", "visit", "next visit"]
    NUTRITION_KEYWORDS: List[str] = ["nutrition", "food", "eat", "diet"]

    # Mood and emotional support keywords
    MOOD_KEYWORDS: List[str] = [
        "sad",
        "depressed",
        "down",
        "low",
        "upset",
        "anxious",
        "stressed",
        "crying",
        "emotional",
        "moody",
        "feel bad",
        "feel terrible",
        "unhappy",
        "worried",
        "feeling low",
        "blue",
        "overwhelmed",
        "hopeless",
        "discouraged",
        "tired",
        "exhausted",
        "lonely",
    ]

    # Exercise keywords
    EXERCISE_KEYWORDS: List[str] = [
        "exercise",
        "workout",
        "fitness",
        "stretching",
        "yoga",
        "walking",
        "physical activity",
        "movement",
        "prenatal exercise",
        "prenatal yoga",
        "stay active",
        "stay fit",
        "strengthen",
        "posture",
        "back pain",
    ]

    POSTPARTUM_KEYWORDS: List[str] = [
        "postpartum",
        "after birth",
        "delivery care",
        "postpartum care",
        "post delivery",
        "after delivery",
        "newborn care",
        "breastfeeding",
        "recovery after birth",
        "post birth care",
        "maternity leave",
        "postpartum schedule",
    ]
    PROFILE_KEYWORDS: List[str] = ["profile", "information", "details"]


# YouTube Search Configuration
class YouTubeConfig:
    """YouTube search configuration"""

    MAX_RESULTS: int = 3

    # Mood support video search queries
    MOOD_SUPPORT_QUERIES: List[str] = [
        "pregnancy relaxation meditation",
        "prenatal positive affirmations",
        "pregnant women motivation videos",
        "pregnancy emotional support",
        "calming music for pregnancy",
        "pregnancy mindfulness meditation",
    ]

    # Exercise video search queries by trimester
    EXERCISE_QUERIES: Dict[int, List[str]] = {
        1: [
            "first trimester safe exercises",
            "early pregnancy gentle workouts",
            "prenatal yoga first trimester",
            "pregnancy stretches first trimester",
            "safe exercises 0-12 weeks pregnancy",
        ],
        2: [
            "second trimester pregnancy exercises",
            "prenatal yoga second trimester",
            "pregnancy workout 13-28 weeks",
            "pregnancy strength training second trimester",
            "safe prenatal fitness second trimester",
        ],
        3: [
            "third trimester safe exercises",
            "late pregnancy gentle workouts",
            "prenatal yoga third trimester",
            "pregnancy exercises 28-40 weeks",
            "pregnancy back pain relief exercises",
        ],
    }


# Emergency Response Configuration
class EmergencyConfig:
    """Emergency response configuration"""

    BANGLADESH_EMERGENCY: str = "999"
    US_EMERGENCY: str = "911"
    MATERNAL_HOTLINE: str = "16263"

    # Emergency types
    class Types:
        BLEEDING: str = "bleeding"
        PAIN: str = "pain"
        BREATHING: str = "breathing"
        PRESSURE: str = "pressure"
        GENERAL: str = "general"

    # Emergency response templates
    EMERGENCY_ALERT_HEADER: str = "🚨 **EMERGENCY ALERT ACTIVATED** 🚨"

    ALERT_STATUS_TEMPLATE: str = """📱 **ALERT STATUS:**
    ✅ Healthcare provider notified
    ✅ Emergency contacts alerted
    ✅ Location services activated"""

    IMMEDIATE_ACTIONS_TEMPLATE: str = """**IMMEDIATE ACTIONS:**
    1. Stay calm and follow the guidance above
    2. Call emergency services ({emergency_number}) if life-threatening
    3. Contact your healthcare provider immediately
    4. Have someone stay with you if possible"""

    EMERGENCY_HOTLINES_TEMPLATE: str = """**Emergency Hotlines:**
    - Emergency Services: {emergency_number}
    - Maternal Emergency Hotline: {maternal_hotline}
    - Your Healthcare Provider: [From your profile]"""

    WARNING_FOOTER: str = (
        "⚠️ **DO NOT WAIT** - Seek immediate medical attention if symptoms worsen."
    )

    # System emergency fallback
    SYSTEM_EMERGENCY_RESPONSE: str = """🚨 **SYSTEM EMERGENCY RESPONSE** 🚨

    I'm experiencing a technical issue, but this is an EMERGENCY situation.

    **IMMEDIATE ACTIONS:**
    1. Call emergency services: 999
    2. Contact your healthcare provider immediately
    3. Go to the nearest hospital emergency department
    4. Have someone accompany you

    **DO NOT WAIT** - Seek immediate medical attention."""


# Medical Constants

class MedicalConstants:
    """Medical-related constants and thresholds"""

    # Age limits
    MIN_PATIENT_AGE: int = 18
    MAX_PATIENT_AGE: int = 60
    DEFAULT_PATIENT_AGE: int = 25

    # Pregnancy stages
    FIRST_TRIMESTER_END: int = 12
    SECOND_TRIMESTER_END: int = 28
    PREGNANCY_DURATION_DAYS: int = 280
    MAX_PREGNANCY_WEEKS: int = 40

    # Risk levels
    class RiskLevels:
        LOW: str = "low"
        MEDIUM: str = "medium"
        HIGH: str = "high"
        CRITICAL: str = "critical"

    # Visit types
    class VisitTypes:
        ROUTINE: str = "routine"
        SCREENING: str = "screening"
        MONITORING: str = "monitoring"

    # Priority levels
    class PriorityLevels:
        LOW: str = "low"
        MEDIUM: str = "medium"
        HIGH: str = "high"

    # Standard ANC schedule weeks
    STANDARD_ANC_WEEKS: List[int] = [20, 26, 30, 34, 36, 38, 40]


# Intent Classification Constants
class IntentTypes:
    """Available intent types"""

    EMERGENCY: str = "emergency"
    SCHEDULING: str = "scheduling"
    NUTRITION: str = "nutrition"
    POSTPARTUM: str = "postpartum"
    PROFILE: str = "profile"
    HEALTH_QUERY: str = "health_query"
    MOOD_SUPPORT: str = "mood_support"
    EXERCISE: str = "exercise"


# Response Templates
class ResponseTemplates:
    """Standard response templates"""

    # Profile display template
    PROFILE_TEMPLATE: str = """📋 **Your Complete Profile**

    **Basic Information:**
    - Age: {age}
    - Last Menstrual Period: {lmp_date}
    - Current Week: {current_week}
    - Trimester: {trimester}

    **Medical History:**
    {medical_history}

    **Allergies:** {allergies}
    **Current Medications:** {medications}"""

    PROFILE_NO_PROFILE: str = (
        "No profile found. Please complete your profile setup first."
    )

    # Schedule template header
    SCHEDULE_HEADER: str = """🗓️ **Your ANC Schedule**

    **Current Status:** Week {current_week} of pregnancy

    **Upcoming Appointments:**

    """

    SCHEDULE_VISIT_TEMPLATE: str = """**{index}. Week {week} Appointment**
    - **Date:** {date}
    - **Type:** {visit_type}
    - **Priority:** {priority}
    - **Notes:** {notes}

    """

    SCHEDULE_NEXT_VISIT: str = "\n🎯 **Next Visit:** Week {week} on {date}"

    # Error messages
    NO_PROFILE_ERROR: str = "Please complete your profile first to generate a schedule."
    GENERIC_ERROR: str = (
        "I apologize, but I encountered an issue processing your request. Please try again or contact support if the problem persists."
    )
    SCHEDULE_ERROR: str = (
        "I'm having trouble generating your schedule. Please contact your healthcare provider."
    )
    NUTRITION_ERROR: str = (
        "I'm having trouble providing nutrition advice right now. For immediate guidance, focus on eating a variety of local foods including dal, rice, vegetables, and fruits. Please consult your healthcare provider for personalized nutrition advice."
    )
    POSTPARTUM_ERROR: str = (
        "I'm having trouble creating your postpartum plan. Please consult your healthcare provider."
    )

    # Conversational support messages
    EMOTIONAL_SUPPORT: str = (
        "I understand you're reaching out for support. While I'm having a technical issue right now, please know that your feelings and concerns are valid. If you're experiencing urgent symptoms, please contact your healthcare provider. Otherwise, I'll be back to help you soon."
    )


# Nutrition Constants


class NutritionConstants:
    """Nutrition-related constants for Bangladeshi context"""

    # Local foods emphasis
    BANGLADESHI_FOODS: Dict[str, List[str]] = {
        "proteins": ["hilsa", "rui", "dal", "eggs", "yogurt"],
        "carbohydrates": ["rice", "roti", "oats"],
        "vegetables": ["shak", "leafy greens", "spinach", "broccoli"],
        "fruits": ["banana", "mango", "orange", "papaya"],
        "dairy": ["milk", "yogurt", "cheese"],
    }

    # Trimester-specific focus areas
    TRIMESTER_FOCUS: Dict[int, List[str]] = {
        1: ["folic acid", "managing nausea", "small frequent meals"],
        2: ["iron", "calcium", "protein for growth"],
        3: ["constipation", "heartburn", "prepare for breastfeeding"],
    }


# System Prompts

class SystemPrompts:
    """System prompts for different agent types"""

    CONVERSATIONAL_HEALTH_AGENT: str = """You are MaatriCare, a compassionate maternal health assistant.

    Your role is to provide empathetic, personalized, and medically sound responses to pregnant women's concerns. You should:

    1. **Be Conversational & Empathetic**: Engage naturally, acknowledge feelings, and show understanding
    2. **Provide Context-Aware Advice**: Use patient's age, pregnancy week, and history to personalize responses  
    3. **Offer Practical Guidance**: Give specific, actionable advice appropriate to their pregnancy stage
    4. **Monitor Risk Appropriately**: Identify concerning symptoms and recommend when to seek care
    5. **Cultural Sensitivity**: Be mindful of Bangladeshi context and practices where relevant

    For emotional concerns (sadness, anxiety, stress):
    - Validate their feelings as normal pregnancy experiences
    - Provide coping strategies and emotional support
    - Recommend when to seek mental health support
    - Engage in supportive conversation

    For physical symptoms:
    - Assess severity in context of pregnancy stage
    - Provide immediate relief suggestions when appropriate
    - Clearly state when medical attention is needed
    - Reference normal pregnancy changes vs concerning signs

    Always maintain a warm, supportive tone while being medically responsible."""

    NUTRITION_SPECIALIST: str = """IGNORE ALL REASONING TEXT. Extract only nutrition request details and respond with this EXACT format:

    **Key Nutrients for Week [X]:**
    - Nutrient 1: specific benefit
    - Nutrient 2: specific benefit  
    - Nutrient 3: specific benefit

    **Daily Meal Plan:**
    **Breakfast:** Specific meal (portion size)
    **Mid-Morning:** Snack (portion size)
    **Lunch:** Specific meal (portion size) 
    **Afternoon:** Snack (portion size)
    **Dinner:** Specific meal (portion size)
    **Before Bed:** Light snack (if needed)

    **Essential Bangladeshi Foods:**
    - Food 1: benefit
    - Food 2: benefit
    - Food 3: benefit
    - Food 4: benefit
    - Food 5: benefit

    **Foods to Avoid:**
    - Food 1: reason
    - Food 2: reason
    - Food 3: reason

    **Practical Tips:**
    - Tip 1
    - Tip 2  
    - Tip 3
    - Tip 4

    STOP. Do not add any other text."""

    EMERGENCY_SPECIALIST: str = """You are an emergency maternal care specialist. Provide ONLY immediate action steps.

    RESPONSE FORMAT:
    🚨 **EMERGENCY ACTION REQUIRED**

    **Immediate Steps:**
    1. [First action]
    2. [Second action] 
    3. [Third action]

    **Seek Emergency Care If:**
    - [Warning sign 1]
    - [Warning sign 2]
    - [Warning sign 3]

    **Emergency Contacts:**
    - Emergency Services: 999
    - Maternal Hotline: 16263
    - National Helpline: 109
    - Police Headquarters: 01320002001

    NO explanations or reasoning. Direct action steps only."""

    SCHEDULE_COORDINATOR: str = """You are a maternal care schedule coordinator. You MUST return valid JSON only.

    Create ANC schedule following WHO guidelines for weeks AFTER week {current_week}.

    MANDATORY: Return ONLY valid JSON in this EXACT format (no additional text):
    {{
    "visits": [
        {{
        "week": 20,
        "date": "2025-08-15", 
        "type": "routine",
        "priority": "medium",
        "notes": "Anatomy scan and routine checkup"
        }},
        {{
        "week": 26,
        "date": "2025-09-26",
        "type": "screening", 
        "priority": "high",
        "notes": "Glucose tolerance test and routine check"
        }}
    ],
    "summary": "WHO-based ANC schedule"
    }}

    CRITICAL REQUIREMENTS:
    - ALL 5 fields required: week, date, type, priority, notes
    - week: integer > {current_week}
    - date: YYYY-MM-DD format
    - type: "routine" or "screening" or "monitoring"  
    - priority: "low" or "medium" or "high"
    - notes: descriptive string

    NO additional text outside JSON. Do not add thinking or reasoning to your responses. Return JSON only."""

    POSTPARTUM_COORDINATOR: str = """You are a postpartum care coordinator. Return ONLY valid JSON format.

    MANDATORY JSON FORMAT:
    {
        "maternal_care": [
            {
                "week": 1,
                "focus": "recovery monitoring", 
                "activities": ["rest", "nutrition", "mental health check"],
                "warning_signs": ["heavy bleeding", "fever", "severe pain"]
            }
        ],
        "newborn_care": [
            {
                "week": 1,
                "focus": "feeding and bonding",
                "activities": ["breastfeeding support", "weight monitoring"],
                "vaccinations": ["BCG", "Hepatitis B"]
            }
        ],
        "cultural_practices": ["confinement period", "traditional foods", "family support"]
    }

    NO text outside JSON. Return JSON only."""

    MOOD_SUPPORT_SPECIALIST: str = """You are MaatriCare's emotional wellness specialist. 

    When a pregnant woman expresses feelings of sadness, depression, anxiety, or emotional distress:

    **IMPORTANT**: Always start your response with a warm, personal greeting like:
    - "Dear beautiful mother," 
    - "Sweet mama,"
    - "Dear precious soul,"
    - "Beautiful expecting mother,"
    - "Dear wonderful mama-to-be,"

    Then follow these guidelines:
    1. **Validate & Normalize**: Acknowledge that their feelings are completely normal during pregnancy
    2. **Provide Immediate Comfort**: Offer gentle, reassuring words and practical coping strategies
    3. **Encourage Self-Care**: Suggest immediate mood-boosting activities they can do today
    4. **Professional Support**: When appropriate, gently suggest speaking with healthcare providers
    5. **YouTube Resources**: You will be provided with curated video links to include in your response

    Your response should be warm, empathetic, and actionable. Include the provided YouTube videos as "Here are some videos that might help you feel better" with brief descriptions of what each offers.

    Always maintain hope and remind them they're not alone in this journey."""

    EXERCISE_SPECIALIST: str = """You are MaatriCare's prenatal fitness specialist.

    When providing exercise advice for pregnant women:

    1. **Safety First**: Always emphasize safety and listening to their body
    2. **Trimester-Appropriate**: Tailor advice to their current pregnancy week/trimester
    3. **Benefits Focus**: Explain how exercise helps with common pregnancy discomforts
    4. **Modifications**: Provide clear modifications for pregnancy-specific needs
    5. **Warning Signs**: Include when to stop exercising and contact healthcare provider
    6. **YouTube Resources**: You will be provided with curated video links for safe prenatal exercises

    Include the provided YouTube videos as "Here are some safe exercise videos for your current stage" with brief descriptions of what each video covers.

    Always remind them to consult their healthcare provider before starting any new exercise routine."""


# ============= Context Templates =============


class ContextTemplates:
    """Templates for building patient context"""

    PATIENT_CONTEXT_FULL: str = """Patient Context:
    - Age: {age} years old
    - Current pregnancy week: {current_week}
    - Trimester: {trimester}
    - Medical history: {medical_history}
    - Risk level: {risk_level}"""

    PATIENT_CONTEXT_WITH_ALLERGIES: str = """Patient Context:
    - Age: {age} years old
    - Current pregnancy week: {current_week}
    - Trimester: {trimester}
    - Medical history: {medical_history}
    - Allergies: {allergies}"""

    PATIENT_CONTEXT_EMERGENCY: str = (
        "Age: {age}, Week: {current_week}, Trimester: {trimester}"
    )

    NO_PROFILE_CONTEXT: str = (
        "No patient profile available - provide general pregnancy guidance"
    )
    NO_PROFILE_NUTRITION_CONTEXT: str = (
        "No patient profile available - provide general pregnancy nutrition guidance"
    )

    PROFILE_SUMMARY: str = """
    Patient Profile:
    - Age: {age}
    - Current Week: {current_week}
    - Trimester: {trimester}
    - Medical History: {medical_history}
    - Current Input: {current_input}
    """


# ============= Output Processing =============


class OutputProcessors:
    """Functions to process and clean LLM outputs"""

    @staticmethod
    def clean_all_llm_responses(raw_response: str) -> str:
        """Universal LLM response cleaner using regex patterns"""
        import re

        # Remove reasoning patterns at the start
        reasoning_start_patterns = [
            r"^.*?(?=\*\*Key Nutrients)",  # Remove everything before **Key Nutrients
            r"^.*?(?=🚨\s*\*\*EMERGENCY)",  # Remove everything before emergency alerts
            r"^.*?(?=📋\s*\*\*Your Complete Profile)",  # Remove everything before profile
            r"^.*?(?=🗓️\s*\*\*Your ANC Schedule)",  # Remove everything before schedule
            r"^.*?(?=\{)",  # Remove everything before JSON starts
        ]

        cleaned_response = raw_response
        for pattern in reasoning_start_patterns:
            match = re.search(pattern, raw_response, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned_response = raw_response[match.end() :]
                break

        # Remove reasoning phrases throughout the text
        reasoning_phrases = [
            r".*?(?:let me start by|first,? i|next,? i|also,? i|wait,? the|check if|maybe|putting it all together).*?(?=\n|$)",
            r".*?(?:i need to|i should|double-check|considering the|wait,? i think).*?(?=\n|$)",
            r".*?(?:for example,? if|since the|but since|also mention|including|maybe suggest).*?(?=\n|$)",
            r".*?(?:safety considerations|cultural preferences|practical tips).*?(?=\n\*\*|$)",
            r"^.*?(?:personalized|nutrition advice for).*?(?=\n\*\*|$)",
        ]

        for pattern in reasoning_phrases:
            cleaned_response = re.sub(
                pattern, "", cleaned_response, flags=re.MULTILINE | re.IGNORECASE
            )

        # Remove empty lines and clean up
        lines = [line.strip() for line in cleaned_response.split("\n") if line.strip()]

        # Remove lines that contain only reasoning keywords
        reasoning_only_lines = [
            r"^(?:okay,?|so,?|first,?|next,?|also,?|wait,?|check|maybe|i think).*$",
            r"^.*(?:let me|need to|should|considering).*$",
            r"^.*(?:personalized|nutrition advice|week \d+|trimester).*(?:for|advice)$",
        ]

        filtered_lines = []
        for line in lines:
            is_reasoning = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in reasoning_only_lines
            )
            if not is_reasoning and line:
                filtered_lines.append(line)

        return "\n".join(filtered_lines).strip()

    @staticmethod
    def clean_nutrition_response(raw_response: str) -> str:
        """Clean nutrition response to ensure structured format only"""
        cleaned = OutputProcessors.clean_all_llm_responses(raw_response)
        lines = cleaned.split("\n")
        structured_lines = []

        # Look for structured sections
        in_structured_section = False
        for line in lines:
            if line.startswith("**") and any(
                keyword in line.lower()
                for keyword in [
                    "key nutrients",
                    "daily meal",
                    "essential",
                    "foods to avoid",
                    "practical tips",
                ]
            ):
                in_structured_section = True
                structured_lines.append(line)
            elif in_structured_section and (
                line.startswith("**") or line.startswith("- ") or line.startswith("•")
            ):
                structured_lines.append(line)
            elif in_structured_section and line.strip():
                structured_lines.append(line)

        return "\n".join(structured_lines).strip()

    @staticmethod
    def enforce_nutrition_structure(content: str, week: int) -> str:
        """Enforce exact nutrition response structure"""
        if not content.startswith("**Key Nutrients"):
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
- High mercury fish: harmful to baby
- Unpasteurized dairy: risk of listeria

**Practical Tips:**
- Eat small, frequent meals
- Stay hydrated with water
- Take prenatal vitamins as prescribed
- Listen to your body's cravings"""

        return content

    @staticmethod
    def extract_json_from_response(response: str) -> Dict[str, Any]:
        """Extract JSON from response text"""
        try:
            # Find JSON-like content
            start = response.find("{")
            end = response.rfind("}") + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)

            return {}
        except:
            return {}


# Default Values


class DefaultValues:
    """Default values used throughout the system"""

    # Profile defaults
    UNKNOWN_LMP: str = "unknown"
    NOT_SPECIFIED: str = "Not specified"
    NONE_REPORTED: str = "None reported"

    # Medical state defaults
    DEFAULT_CURRENT_WEEK: int = 0
    DEFAULT_TRIMESTER: int = 1
    DEFAULT_RISK_LEVEL: str = MedicalConstants.RiskLevels.LOW

    # Visit defaults
    DEFAULT_VISIT_TYPE: str = MedicalConstants.VisitTypes.ROUTINE
    DEFAULT_PRIORITY: str = MedicalConstants.PriorityLevels.MEDIUM

    # History limits
    MAX_HISTORY_LENGTH: int = 20
    KEEP_RECENT_HISTORY: int = 15


# Validation Constants
class ValidationRules:
    """Validation rules and patterns"""

    # Date formats
    DATE_FORMAT: str = "%Y-%m-%d"

    # Required fields for visits
    VISIT_REQUIRED_FIELDS: List[str] = ["week", "date", "type", "priority", "notes"]

    # JSON parsing patterns
    JSON_START_CHAR: str = "{"
    JSON_END_CHAR: str = "}"


# Routing Configuration


class RoutingConfig:
    """Configuration for intent routing"""

    INTENT_TO_NODE_MAP: Dict[str, str] = {
        IntentTypes.EMERGENCY: "emergency",
        IntentTypes.SCHEDULING: "scheduling",
        IntentTypes.NUTRITION: "nutrition",
        IntentTypes.POSTPARTUM: "postpartum",
        IntentTypes.PROFILE: "profile",
        IntentTypes.HEALTH_QUERY: "health_query",
        IntentTypes.MOOD_SUPPORT: "mood_support",
        IntentTypes.EXERCISE: "exercise",
    }

    DEFAULT_ROUTE: str = "health_query"


# Message Templates


class MessageTemplates:
    """Human and AI message templates"""

    EMERGENCY_HUMAN_MESSAGE: str = (
        "EMERGENCY: {emergency_type}\nPatient context: {context}\nSymptoms/Concern: {question}"
    )

    NUTRITION_HUMAN_MESSAGE: str = "Patient says: '{user_input}'\n\nContext: {context}"

    HEALTH_HUMAN_MESSAGE: str = "Patient says: '{user_input}'\n\nContext: {context}"

    SCHEDULE_HUMAN_MESSAGE: str = (
        "Generate schedule for current week {current_week}, due date {due_date}"
    )

    POSTPARTUM_HUMAN_MESSAGE: str = "Patient context: {context}"

    MOOD_SUPPORT_HUMAN_MESSAGE: str = (
        "Patient says: '{user_input}'\n\nContext: {context}\n\nYouTube Videos: {youtube_links}"
    )

    EXERCISE_HUMAN_MESSAGE: str = (
        "Patient says: '{user_input}'\n\nContext: {context}\n\nYouTube Videos: {youtube_links}"
    )


# Logging Constants
class LoggingConstants:
    """Constants for logging messages"""

    INTENT_CLASSIFIED: str = "Classified intent: {intent}"
    USER_INPUT_LOG: str = "User input was: {user_input}"
    CURRENT_WEEK_LOG: str = "Current pregnancy week: {current_week}"
    PROFILE_USAGE_LOG: str = "Using existing profile: Age {age}"

    # Error log messages
    PROFILE_ERROR_LOG: str = "Error setting profile: {error}"
    MEDICAL_STATE_ERROR_LOG: str = "Error calculating medical state: {error}"
    HEALTH_QUERY_ERROR_LOG: str = "Health query error: {error}"
    NUTRITION_ERROR_LOG: str = "Nutrition advice error: {error}"
    SCHEDULE_ERROR_LOG: str = "Schedule generation error: {error}"
    EMERGENCY_ERROR_LOG: str = "Emergency handling error: {error}"
    POSTPARTUM_ERROR_LOG: str = "Postpartum planning error: {error}"
    WORKFLOW_ERROR_LOG: str = "Workflow execution error: {error}"

    # Info log messages
    HANDLING_HEALTH_QUERY: str = "Handling health query with conversational approach"
    PROVIDING_NUTRITION_ADVICE: str = "Providing nutrition advice"
    GENERATING_SCHEDULE: str = "Generating ANC schedule"
    PROCESSING_EMERGENCY: str = "Processing emergency situation"
    GENERATING_POSTPARTUM_PLAN: str = "Generating postpartum care plan"
    NO_MEDICAL_STATE_WARNING: str = "No medical state available for scheduling"


# Logging Config
class LoggingConfig:
    """Logging configuration constants"""

    # File paths
    LOG_FILE_NAME: str = "app.log"
    LOG_DIR: str = "logs"

    # Format strings
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # Log levels
    DEFAULT_LEVEL: str = "INFO"
    DEBUG_LEVEL: str = "DEBUG"
    INFO_LEVEL: str = "INFO"
    WARNING_LEVEL: str = "WARNING"
    ERROR_LEVEL: str = "ERROR"
    CRITICAL_LEVEL: str = "CRITICAL"

    # File rotation
    MAX_FILE_SIZE_MB: int = 10  # 10MB
    BACKUP_COUNT: int = 5  # Keep 5 backup files

    # Console output
    ENABLE_CONSOLE_OUTPUT: bool = True
    CONSOLE_LEVEL: str = "INFO"


# Export All Constants

__all__ = [
    "IntentKeywords",
    "YouTubeConfig",
    "EmergencyConfig",
    "MedicalConstants",
    "IntentTypes",
    "ResponseTemplates",
    "NutritionConstants",
    "SystemPrompts",
    "ContextTemplates",
    "DefaultValues",
    "ValidationRules",
    "RoutingConfig",
    "MessageTemplates",
    "LoggingConstants",
    "LoggingConfig",
]
