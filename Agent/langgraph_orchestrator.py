import logging
import datetime
import json
import operator
from typing import Dict, List, Optional, Any, TypedDict, Annotated, Literal
from dataclasses import dataclass
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Command
from pydantic import BaseModel, Field

# Local imports
from Service.llm_service import langgraph_llm
from Utils.constants import (
    IntentKeywords,
    EmergencyConfig,
    MedicalConstants,
    IntentTypes,
    ResponseTemplates,
    SystemPrompts,
    ContextTemplates,
    DefaultValues,
    ValidationRules,
    MessageTemplates,
)
from Utils.output_processors import OutputProcessors
from Utils.logging_config import get_logger
from Utils.youtube_search import youtube_service

# Configure logging
logger = get_logger(__name__)


# ============= State Definitions =============


class ConversationState(TypedDict):
    """Main conversation state"""

    user_input: str
    patient_profile: Optional[Dict[str, Any]]
    medical_state: Optional[Dict[str, Any]]
    intent: str
    context_data: Annotated[List[Dict], operator.add]  # Workers write data here
    final_response: str


class WorkerState(TypedDict):
    """State for individual workers"""

    user_input: str
    patient_profile: Optional[Dict[str, Any]]
    medical_state: Optional[Dict[str, Any]]
    worker_type: str
    context_data: Annotated[List[Dict], operator.add]


# ============= Data Models =============

class PatientProfile(BaseModel):
    """Patient profile data model"""

    name: Optional[str] = None
    age: int = Field(
        ge=MedicalConstants.MIN_PATIENT_AGE, le=MedicalConstants.MAX_PATIENT_AGE
    )
    lmp_date: str
    medical_history: str = DefaultValues.NOT_SPECIFIED
    allergies: List[str] = []
    medications: List[str] = []
    bmi: Optional[float] = None
    blood_type: Optional[str] = None


class MedicalState(BaseModel):
    """Current medical state of the patient"""

    current_week: int = DefaultValues.DEFAULT_CURRENT_WEEK
    trimester: int = DefaultValues.DEFAULT_TRIMESTER
    due_date: Optional[str] = None
    risk_level: str = DefaultValues.DEFAULT_RISK_LEVEL
    last_assessment: Optional[str] = None


class PatientContextManager:
    """Manages patient context and conversation history - simplified for orchestrator pattern"""

    def __init__(self):
        self.current_profile: Optional[Dict[str, Any]] = None
        self.current_medical_state: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Dict[str, Any]] = []
        self.logger = get_logger("MaatriCare.ContextManager")

    @property
    def state(self) -> Dict[str, Any]:
        """Property to access current state as a dictionary for UI compatibility"""
        return {
            "profile": self.current_profile,
            "medical_state": self.current_medical_state,
        }

    def set_profile(self, profile_data: Dict[str, Any]) -> None:
        """Set patient profile and calculate medical state"""
        try:
            # Validate profile data
            profile = PatientProfile(**profile_data)
            medical_state = self._calculate_medical_state(profile)

            self.current_profile = profile_data
            self.current_medical_state = medical_state.dict()

            self.logger.info(
                f"Profile set for patient age {profile.age}, week {medical_state.current_week}"
            )

        except Exception as e:
            self.logger.error(f"Error setting profile: {e}")
            self.current_profile = None
            self.current_medical_state = None

    def _calculate_medical_state(self, profile: PatientProfile) -> MedicalState:
        """Calculate medical state from profile"""
        if profile.lmp_date == DefaultValues.UNKNOWN_LMP:
            return MedicalState()

        try:
            lmp = datetime.datetime.strptime(
                profile.lmp_date, ValidationRules.DATE_FORMAT
            )
            today = datetime.datetime.now()
            days_pregnant = (today - lmp).days
            current_week = days_pregnant // 7

            # Calculate trimester
            if current_week <= MedicalConstants.FIRST_TRIMESTER_END:
                trimester = 1
            elif current_week <= MedicalConstants.SECOND_TRIMESTER_END:
                trimester = 2
            else:
                trimester = 3

            # Calculate due date
            due_date = (
                lmp + datetime.timedelta(days=MedicalConstants.PREGNANCY_DURATION_DAYS)
            ).strftime(ValidationRules.DATE_FORMAT)

            return MedicalState(
                current_week=current_week, trimester=trimester, due_date=due_date
            )

        except ValueError as e:
            self.logger.error(f"Error calculating medical state: {e}")
            return MedicalState()

    def get_context_summary(self, user_input: str) -> str:
        """Get formatted context summary"""
        if not self.current_profile or not self.current_medical_state:
            return ContextTemplates.NO_PROFILE_CONTEXT

        return ContextTemplates.PATIENT_CONTEXT_FULL.format(
            age=self.current_profile.get("age", "unknown"),
            current_week=self.current_medical_state.get("current_week", 0),
            trimester=self.current_medical_state.get("trimester", 1),
            medical_history=self.current_profile.get("medical_history", "None"),
            risk_level=self.current_medical_state.get("risk_level", "low"),
        )

    def add_interaction(self, user_input: str, response: str, metadata: Dict = None):
        """Add interaction to history"""
        interaction = {
            "user_input": user_input,
            "response": response,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.conversation_history.append(interaction)


# ============= Worker Functions =============


def intent_classifier(
    state: ConversationState,
) -> Command[
    Literal[
        "nutrition_worker",
        "exercise_worker",
        "mood_support_worker",
        "scheduling_worker",
        "emergency_worker",
        "general_worker",
    ]
]:
    """Classify user intent based on input"""
    user_input = state["user_input"].lower()

    # Emergency detection
    if any(keyword in user_input for keyword in IntentKeywords.EMERGENCY_KEYWORDS):
        return Command(goto="emergency_worker", update={"intent": "emergency"})

    # Nutrition keywords
    nutrition_indicators = [
        "food",
        "eat",
        "diet",
        "nutrition",
        "meal",
        "hungry",
        "appetite",
        "vitamin",
        "recipe",
        "breakfast",
        "lunch",
        "dinner",
    ]
    if any(keyword in user_input for keyword in nutrition_indicators):
        return Command(goto="nutrition_worker", update={"intent": "nutrition"})

    # Exercise keywords
    exercise_indicators = [
        "exercise",
        "workout",
        "yoga",
        "walk",
        "fitness",
        "active",
        "movement",
        "stretch",
    ]
    if any(keyword in user_input for keyword in exercise_indicators):
        return Command(goto="exercise_worker", update={"intent": "exercise"})

    # Mood/emotional keywords
    mood_keywords = [
        "feel",
        "feeling",
        "sad",
        "depressed",
        "anxious",
        "worried",
        "scared",
        "upset",
        "emotional",
        "mood",
        "stress",
    ]
    if any(keyword in user_input for keyword in mood_keywords):
        return Command(goto="mood_support_worker", update={"intent": "mood_support"})

    # Scheduling keywords
    scheduling_indicators = [
        "appointment",
        "schedule",
        "visit",
        "checkup",
        "doctor",
        "anc",
        "when should",
    ]
    if any(keyword in user_input for keyword in scheduling_indicators):
        return Command(goto="scheduling_worker", update={"intent": "scheduling"})

    return Command(goto="general_worker", update={"intent": "general_health"})


def nutrition_worker(state: ConversationState) -> Command[Literal["orchestrator"]]:
    """Worker that fetches nutrition information"""
    try:
        user_input = state["user_input"]
        patient_profile = state.get("patient_profile")
        medical_state = state.get("medical_state")

        if patient_profile and medical_state:
            context = f"Age: {patient_profile.get('age')}, Week: {medical_state.get('current_week')}, Trimester: {medical_state.get('trimester')}"
        else:
            context = "No specific patient context"

        nutrition_data = {
            "type": "nutrition_info",
            "trimester": medical_state.get("trimester", 2) if medical_state else 2,
            "week": medical_state.get("current_week", 20) if medical_state else 20,
            "context": context,
            "foods_to_focus": _get_trimester_foods(
                medical_state.get("trimester", 2) if medical_state else 2
            ),
            "bangladeshi_foods": [
                "dal",
                "rice",
                "fish",
                "vegetables",
                "fruits",
                "milk",
                "eggs",
            ],
            "user_query": user_input,
        }

        return Command(goto="orchestrator", update={"context_data": [nutrition_data]})

    except Exception as e:
        logger.error(f"Nutrition worker error: {e}")
        return Command(
            goto="orchestrator",
            update={"context_data": [{"type": "nutrition_info", "error": str(e)}]},
        )


def exercise_worker(state: ConversationState) -> Command[Literal["orchestrator"]]:
    """Worker that fetches exercise information"""
    try:
        medical_state = state.get("medical_state")
        trimester = medical_state.get("trimester", 2) if medical_state else 2
        week = medical_state.get("current_week", 20) if medical_state else 20

        videos = []
        try:
            videos = youtube_service.search_exercise_videos(trimester, week)
        except Exception as video_error:
            logger.warning(f"Could not fetch exercise videos: {video_error}")

        exercise_data = {
            "type": "exercise_info",
            "trimester": trimester,
            "week": week,
            "videos": videos,
            "safe_exercises": _get_safe_exercises(trimester),
            "user_query": state["user_input"],
        }

        return Command(goto="orchestrator", update={"context_data": [exercise_data]})

    except Exception as e:
        logger.error(f"Exercise worker error: {e}")
        return Command(
            goto="orchestrator",
            update={"context_data": [{"type": "exercise_info", "error": str(e)}]},
        )


def mood_support_worker(state: ConversationState) -> Command[Literal["orchestrator"]]:
    """Worker that fetches mood support information"""
    try:
        videos = []
        try:
            videos = youtube_service.search_mood_support_videos()
        except Exception as video_error:
            logger.warning(f"Could not fetch mood videos: {video_error}")

        mood_data = {
            "type": "mood_support_info",
            "videos": videos,
            "coping_strategies": [
                "deep breathing",
                "gentle exercise",
                "talking to loved ones",
                "rest",
            ],
            "user_query": state["user_input"],
        }

        return Command(goto="orchestrator", update={"context_data": [mood_data]})

    except Exception as e:
        logger.error(f"Mood support worker error: {e}")
        return Command(
            goto="orchestrator",
            update={"context_data": [{"type": "mood_support_info", "error": str(e)}]},
        )


def scheduling_worker(state: ConversationState) -> Command[Literal["orchestrator"]]:
    """Worker that fetches ANC scheduling information"""
    try:
        medical_state = state.get("medical_state")
        if not medical_state:
            return Command(
                goto="orchestrator",
                update={
                    "context_data": [
                        {
                            "type": "scheduling_info",
                            "error": "No medical state available",
                        }
                    ]
                },
            )

        current_week = medical_state.get("current_week", 0)

        schedule_data = {
            "type": "scheduling_info",
            "current_week": current_week,
            "next_visits": _get_next_anc_visits(current_week),
            "user_query": state["user_input"],
        }

        return Command(goto="orchestrator", update={"context_data": [schedule_data]})

    except Exception as e:
        logger.error(f"Scheduling worker error: {e}")
        return Command(
            goto="orchestrator",
            update={"context_data": [{"type": "scheduling_info", "error": str(e)}]},
        )


def emergency_worker(state: ConversationState) -> Command[Literal["orchestrator"]]:
    """Worker that handles emergency information"""
    emergency_data = {
        "type": "emergency_info",
        "emergency_numbers": {"emergency": "999", "maternal_hotline": "16263"},
        "immediate_actions": [
            "Stay calm",
            "Call emergency services if life-threatening",
            "Contact healthcare provider",
            "Have someone stay with you",
        ],
        "user_query": state["user_input"],
    }

    return Command(goto="orchestrator", update={"context_data": [emergency_data]})


def general_worker(state: ConversationState) -> Command[Literal["orchestrator"]]:
    """Worker that handles general health queries"""
    general_data = {
        "type": "general_health_info",
        "common_topics": [
            "pregnancy symptoms",
            "baby development",
            "health monitoring",
            "lifestyle advice",
        ],
        "user_query": state["user_input"],
    }

    return Command(goto="orchestrator", update={"context_data": [general_data]})


# ============= Helper Functions =============


def _get_trimester_foods(trimester: int) -> List[str]:
    """Get trimester-specific food recommendations"""
    foods_by_trimester = {
        1: ["ginger tea", "crackers", "bananas", "toast", "small frequent meals"],
        2: ["iron-rich foods", "calcium sources", "protein", "folate-rich vegetables"],
        3: [
            "fiber-rich foods",
            "small meals",
            "hydrating foods",
            "energy-dense snacks",
        ],
    }
    return foods_by_trimester.get(trimester, foods_by_trimester[2])


def _get_safe_exercises(trimester: int) -> List[str]:
    """Get trimester-specific safe exercises"""
    exercises_by_trimester = {
        1: ["walking", "gentle stretching", "prenatal yoga", "swimming"],
        2: ["prenatal yoga", "walking", "swimming", "light strength training"],
        3: ["gentle walking", "prenatal yoga", "pelvic floor exercises", "stretching"],
    }
    return exercises_by_trimester.get(trimester, exercises_by_trimester[2])


def _get_next_anc_visits(current_week: int) -> List[Dict]:
    """Get next ANC visit recommendations"""
    standard_weeks = [20, 26, 30, 34, 36, 38, 40]
    next_visits = [week for week in standard_weeks if week > current_week]

    visits = []
    for week in next_visits[:3]:
        date = (
            datetime.datetime.now() + datetime.timedelta(weeks=(week - current_week))
        ).strftime("%Y-%m-%d")
        visits.append(
            {
                "week": week,
                "date": date,
                "type": "routine" if week not in [26, 34] else "screening",
                "priority": "high" if week in [26, 34, 36] else "medium",
            }
        )

    return visits


# ============= Orchestrator Function =============


def orchestrator(state: ConversationState) -> Command[Literal["__end__"]]:
    """Main orchestrator that generates the final response using worker data"""
    try:
        user_input = state["user_input"]
        intent = state["intent"]
        context_data = state.get("context_data", [])
        patient_profile = state.get("patient_profile")
        medical_state = state.get("medical_state")

        if patient_profile and medical_state:
            context_summary = f"Patient: Age {patient_profile.get('age')}, Week {medical_state.get('current_week')}, Trimester {medical_state.get('trimester')}"
        else:
            context_summary = "No patient profile available"

        if intent == "emergency":
            response = _generate_emergency_response(
                user_input, context_data, context_summary
            )
        elif intent == "nutrition":
            response = _generate_nutrition_response(
                user_input, context_data, context_summary
            )
        elif intent == "exercise":
            response = _generate_exercise_response(
                user_input, context_data, context_summary
            )
        elif intent == "mood_support":
            response = _generate_mood_response(
                user_input, context_data, context_summary
            )
        elif intent == "scheduling":
            response = _generate_scheduling_response(
                user_input, context_data, context_summary
            )
        else:
            response = _generate_general_response(user_input, context_summary)

        return Command(goto="__end__", update={"final_response": response})

    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        return Command(
            goto="__end__",
            update={
                "final_response": "I apologize, but I'm having trouble processing your request right now. Please try again or contact your healthcare provider if this is urgent."
            },
        )


def _generate_emergency_response(
    user_input: str, context_data: List[Dict], context_summary: str
) -> str:
    """Generate emergency response using LLM"""
    try:
        emergency_info = next(
            (data for data in context_data if data.get("type") == "emergency_info"), {}
        )

        emergency_prompt = f"""You are MaatriCare, a compassionate AI agent for pregnant women in Bangladesh. 
        
        URGENT: The user has indicated an emergency situation. Respond with immediate care while prioritizing safety.

        User Question: {user_input}
        Context Summary: {context_summary}
        Emergency Information: {emergency_info}

        IMPORTANT: Provide a caring but urgent response using STRUCTURED MARKDOWN format:

        **🚨 EMERGENCY RESPONSE 🚨**

        **Immediate Assessment:**
        Acknowledge their situation with empathy

        **Critical Actions:**
        1. First immediate action
        2. Second immediate action
        3. Third immediate action

        **Safety Guidelines:**
        - Safety point 1
        - Safety point 2
        - Safety point 3

        **When to Call Emergency Services (999):**
        - Emergency condition 1
        - Emergency condition 2
        
        **Thinking and Reasoning**
        - Do not add any thinking and reasoning steps in the response.
        
        **Language**
        - Use English language only.
       

        Use caring, supportive language and provide immediate actionable guidance. Focus on safety first."""

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=emergency_prompt)]
        response = langgraph_llm.invoke(messages)
        cleared_response = OutputProcessors.clean_all_llm_responses(response.content)

        emergency_footer = f"""

        🚨 **EMERGENCY CONTACTS:**
        - Emergency Services: 999
        - Maternal Emergency Hotline: 16263
        - National Emergency Service: 999

        ⚠️ **DO NOT WAIT** - Seek immediate medical attention if symptoms worsen."""

        return cleared_response + emergency_footer

    except Exception as e:
        logger.error(f"Emergency response generation error: {e}")
        return """🚨 **EMERGENCY ALERT** 🚨

        Call emergency services (999) immediately if this is life-threatening.
        Contact your healthcare provider right away.

        Emergency Services: 999
        Maternal Emergency Hotline: 16263

        ⚠️ DO NOT WAIT - Seek immediate medical attention."""


def _generate_nutrition_response(
    user_input: str, context_data: List[Dict], context_summary: str
) -> str:
    """Generate nutrition response using LLM and worker data"""
    try:
        nutrition_info = next(
            (data for data in context_data if data.get("type") == "nutrition_info"), {}
        )

        if nutrition_info.get("error"):
            return ResponseTemplates.NUTRITION_ERROR

        nutrition_prompt = f"""You are MaatriCare, a compassionate AI agent for pregnant women in Bangladesh.

        User Question: {user_input}
        Context Summary: {context_summary}
        Nutrition Information: {nutrition_info}

        IMPORTANT: Provide personalized nutrition advice using STRUCTURED MARKDOWN format:

        **🥗 Nutrition Guidance**

        **Your Current Needs:**
        Address their specific question naturally

        **Key Nutrients This Week:**
        - **Nutrient 1:** Benefits and why important
        - **Nutrient 2:** Benefits and why important  
        - **Nutrient 3:** Benefits and why important

        **Recommended Bangladeshi Foods:**
        - **Food 1:** Nutritional benefits
        - **Food 2:** Nutritional benefits
        - **Food 3:** Nutritional benefits

        **Sample Daily Meal Plan:**
        **Breakfast:** Specific meal with portions
        **Mid-Morning:** Snack suggestion
        **Lunch:** Main meal with vegetables
        **Afternoon:** Healthy snack
        **Dinner:** Balanced evening meal
        **Before Bed:** Optional evening snack

        **Important Tips:**
        - Practical tip 1
        - Practical tip 2
        - Foods to limit/avoid if relevant
        
        **Thinking and Reasoning**
        - Do not add any thinking and reasoning steps in the response.
        
        **Language**
        - Use English language only.

        Use warm, supportive tone like talking to a friend. Make it feel conversational, not template-like."""

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=nutrition_prompt)]
        response = langgraph_llm.invoke(messages)
        cleared_response = OutputProcessors.clean_all_llm_responses(response.content)
        return cleared_response

    except Exception as e:
        logger.error(f"Nutrition response generation error: {e}")
        return "I'd be happy to help with nutrition advice! For your pregnancy stage, focus on iron-rich foods like leafy greens, protein from fish and eggs, and plenty of fruits. Traditional Bangladeshi foods like dal, rice, fish curry, and seasonal vegetables are excellent choices. Stay hydrated and eat small, frequent meals. Would you like specific meal suggestions?"


def _generate_exercise_response(
    user_input: str, context_data: List[Dict], context_summary: str
) -> str:
    """Generate exercise response using LLM and worker data"""
    try:
        exercise_info = next(
            (data for data in context_data if data.get("type") == "exercise_info"), {}
        )

        if exercise_info.get("error"):
            return "I recommend gentle walking, prenatal yoga, and stretching. Always consult your healthcare provider before starting any exercise routine."

        exercise_prompt = f"""You are MaatriCare, a compassionate AI agent for pregnant women in Bangladesh.

        User Question: {user_input}
        Context Summary: {context_summary}
        Exercise Information: {exercise_info}

        IMPORTANT: Provide personalized exercise guidance using STRUCTURED MARKDOWN format:

        **🤸‍♀️ Safe Exercise Guide**

        **Your Exercise Question:**
        Respond to their specific question naturally

        **Recommended Activities:**
        - **Activity 1:** Benefits and why safe
        - **Activity 2:** Benefits and why safe  
        - **Activity 3:** Benefits and why safe

        **Safety Guidelines:**
        - **Listen to your body:** Stop if you feel unwell
        - **Stay hydrated:** Important during exercise
        - **Avoid overheating:** Keep cool and comfortable
        - **Consult provider:** Check before starting new routines

        **Helpful Resources:**
        Include any video links if available from exercise_info

        **Trimester-Specific Tips:**
        Provide relevant advice for their current stage
        
        **Thinking and Reasoning**
        - Do not add any thinking and reasoning steps in the response.
        
        **Language**
        - Use English language only.

        Use encouraging, supportive language and make it feel like advice from a caring friend."""

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=exercise_prompt)]
        response = langgraph_llm.invoke(messages)
        cleared_response = OutputProcessors.clean_all_llm_responses(response.content)
        return cleared_response

    except Exception as e:
        logger.error(f"Exercise response generation error: {e}")
        return "For safe pregnancy exercise, I recommend gentle walking, prenatal yoga, and light stretching. Swimming is also wonderful if you have access. Always listen to your body, stay hydrated, and check with your healthcare provider before starting any new routine. Would you like specific exercise suggestions for your stage of pregnancy?"


def _generate_mood_response(
    user_input: str, context_data: List[Dict], context_summary: str
) -> str:
    """Generate mood support response using LLM"""
    try:
        mood_info = next(
            (data for data in context_data if data.get("type") == "mood_support_info"),
            {},
        )

        mood_prompt = f"""You are MaatriCare, a compassionate AI agent for pregnant women in Bangladesh.

        User Question: {user_input}
        Context Summary: {context_summary}
        Mood Support Information: {mood_info}

        IMPORTANT: Provide emotional support using STRUCTURED MARKDOWN format:

        **💝 Emotional Support**

        **Understanding Your Feelings:**
        Acknowledge their specific emotional concern with empathy

        **You're Not Alone:**
        Validate that their feelings are completely normal during pregnancy

        **Gentle Coping Strategies:**
        - **Deep Breathing:** Take slow, calming breaths
        - **Gentle Movement:** Light walking or stretching
        - **Connection:** Reach out to loved ones
        - **Rest:** Give yourself permission to rest

        **Helpful Resources:**
        Include any video links if available from mood_info

        **When to Seek Additional Help:**
        - If feelings persist for more than 2 weeks
        - If you feel unable to care for yourself
        - If you have thoughts of harming yourself or baby
        
        **Thinking and Reasoning**
        - Do not add any thinking and reasoning steps in the response.
        
        **Language**
        - Use English language only.

        Use warm, supportive language like a caring friend who truly understands."""

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=mood_prompt)]
        response = langgraph_llm.invoke(messages)
        cleared_response = OutputProcessors.clean_all_llm_responses(response.content)

        support_footer = "\n\nRemember, you're not alone in this journey, and it's completely okay to ask for help. If these feelings persist or worsen, please reach out to your healthcare provider. You're doing wonderfully. 💕"

        return cleared_response + support_footer

    except Exception as e:
        logger.error(f"Mood response generation error: {e}")
        return "I can hear that you're going through a tough time, and I want you to know that what you're feeling is completely normal during pregnancy. Your emotions are valid, and it's okay to have difficult days. Try taking some slow, deep breaths and remember that you're stronger than you know. Would you like to talk about what's specifically bothering you today? 💕"


def _generate_scheduling_response(
    user_input: str, context_data: List[Dict], context_summary: str
) -> str:
    """Generate scheduling response using LLM"""
    try:
        schedule_info = next(
            (data for data in context_data if data.get("type") == "scheduling_info"), {}
        )

        if schedule_info.get("error"):
            return ResponseTemplates.SCHEDULE_ERROR

        schedule_prompt = f"""You are MaatriCare, a compassionate AI agent for pregnant women in Bangladesh.

        User Question: {user_input}
        Context Summary: {context_summary}
        Schedule Information: {schedule_info}

        IMPORTANT: Provide scheduling guidance using STRUCTURED MARKDOWN format:

        **📅 Your ANC Schedule**

        **Current Status:**
        Address their scheduling question naturally

        **Upcoming Appointments:**
        - **Week X Appointment:** Date and type of visit
        - **Week Y Appointment:** Date and type of visit
        - **Week Z Appointment:** Date and type of visit

        **What to Expect:**
        - Routine monitoring and health assessment
        - Growth and development checks
        - Important screenings at key weeks

        **Preparation Tips:**
        - Bring your ANC card and any medications
        - Prepare questions about your health
        - Arrange transportation in advance

        **Important Reminders:**
        - Regular checkups are vital for you and baby
        - Don't miss key screening appointments
        - Contact clinic if you need to reschedule
        
        **Thinking and Reasoning**
        - Do not add any thinking and reasoning steps in the response.
        
        **Language**
        - Use English language only.

        Make the schedule feel manageable and reassuring, not overwhelming."""

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=schedule_prompt)]
        response = langgraph_llm.invoke(messages)
        cleared_response = OutputProcessors.clean_all_llm_responses(response.content)
        return cleared_response

    except Exception as e:
        logger.error(f"Scheduling response generation error: {e}")
        return "I'd be happy to help you keep track of your ANC appointments! Regular checkups are so important for you and your baby's health. Would you like me to help you understand when your next appointment should be, or do you have questions about what to expect during these visits?"


def _generate_general_response(user_input: str, context_summary: str) -> str:
    """Generate general health response using LLM"""
    try:
        general_prompt = f"""You are MaatriCare, a compassionate AI agent for pregnant women in Bangladesh.

        User Question: {user_input}
        Context Summary: {context_summary}

        IMPORTANT: Provide general health guidance using STRUCTURED MARKDOWN format:

        **🩺 Health Information**

        **Your Question:**
        Address their specific question naturally and conversationally

        **Key Information:**
        - **Point 1:** Relevant health information
        - **Point 2:** Practical advice
        - **Point 3:** Important considerations

        **For Your Stage:**
        Provide advice relevant to their pregnancy stage

        **Important Reminders:**
        - Always consult your healthcare provider for medical concerns
        - Trust your instincts about your body
        - Regular checkups are important

        **When to Contact Your Doctor:**
        - If symptoms worsen or change
        - If you have new concerns
        - For routine appointment scheduling
        
        **Thinking and Reasoning**
        - Do not add any thinking and reasoning steps in the response. 
        
        **Language**
        - Use English language only. 

        Use warm, supportive language like a knowledgeable friend who genuinely cares about their wellbeing."""

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=general_prompt)]
        result = langgraph_llm.invoke(messages)

        return OutputProcessors.clean_all_llm_responses(result.content)

    except Exception as e:
        logger.error(f"General response error: {e}")
        return "I'm here to help with your pregnancy journey! Whether you have questions about health, nutrition, exercise, or just need someone to talk to, I'm here for you. What would you like to know more about?"


# ============= Main Orchestrator Class =============

class MaatriCareLangGraphNativeOrchestrator:
    """
    New orchestrator-worker pattern implementation for MaatriCare
    """

    def __init__(self):
        self.logger = get_logger("MaatriCare.OrchestatorWorker")
        self.context_manager = PatientContextManager()
        self.workflow = self._build_workflow()
        self.logger.info("Initialized Orchestrator-Worker pattern")

    def _build_workflow(self) -> StateGraph:
        """Build the orchestrator-worker workflow"""
        workflow = StateGraph(ConversationState)

        workflow.add_node("intent_classifier", intent_classifier)
        workflow.add_node("nutrition_worker", nutrition_worker)
        workflow.add_node("exercise_worker", exercise_worker)
        workflow.add_node("mood_support_worker", mood_support_worker)
        workflow.add_node("scheduling_worker", scheduling_worker)
        workflow.add_node("emergency_worker", emergency_worker)
        workflow.add_node("general_worker", general_worker)
        workflow.add_node("orchestrator", orchestrator)

        workflow.add_edge(START, "intent_classifier")

        workflow.add_edge("nutrition_worker", "orchestrator")
        workflow.add_edge("exercise_worker", "orchestrator")
        workflow.add_edge("mood_support_worker", "orchestrator")
        workflow.add_edge("scheduling_worker", "orchestrator")
        workflow.add_edge("emergency_worker", "orchestrator")
        workflow.add_edge("general_worker", "orchestrator")

        workflow.add_edge("orchestrator", END)

        return workflow.compile()

    @property
    def state(self) -> Dict[str, Any]:
        """Get current state for UI compatibility"""
        return self.context_manager.state

    def set_profile(self, profile_data: Dict[str, Any]) -> None:
        """Set patient profile"""
        self.context_manager.set_profile(profile_data)
        self.logger.info("Profile updated in orchestrator")

    def process_query(self, user_input: str) -> str:
        """Process user query through orchestrator-worker pattern"""
        try:
            state = {
                "user_input": user_input,
                "patient_profile": self.context_manager.current_profile,
                "medical_state": self.context_manager.current_medical_state,
                "intent": "",
                "context_data": [],
                "final_response": "",
            }

            result = self.workflow.invoke(state)
            response = result.get(
                "final_response", "I'm sorry, I couldn't process your request."
            )

            self.context_manager.add_interaction(user_input, response)

            return response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            error_response = "I apologize, but I'm having trouble processing your request. Please try again."
            self.context_manager.add_interaction(user_input, error_response)
            return error_response

    def get_profile_display(self) -> str:
        """Get formatted profile display"""
        if not self.context_manager.current_profile:
            return ResponseTemplates.PROFILE_NO_PROFILE

        profile = self.context_manager.current_profile
        medical_state = self.context_manager.current_medical_state or {}

        allergies = (
            ", ".join(profile.get("allergies", [])) or DefaultValues.NONE_REPORTED
        )
        medications = (
            ", ".join(profile.get("medications", [])) or DefaultValues.NONE_REPORTED
        )

        return ResponseTemplates.PROFILE_TEMPLATE.format(
            age=profile.get("age", "Unknown"),
            lmp_date=profile.get("lmp_date", DefaultValues.UNKNOWN_LMP),
            current_week=medical_state.get("current_week", 0),
            trimester=medical_state.get("trimester", 1),
            medical_history=profile.get("medical_history", DefaultValues.NOT_SPECIFIED),
            allergies=allergies,
            medications=medications,
        )


# ============= Exports =============

# For backward compatibility
MaatriCareLangGraphOrchestrator = MaatriCareLangGraphNativeOrchestrator

# Main exports for compatibility
__all__ = [
    "MaatriCareLangGraphNativeOrchestrator",
    "PatientContextManager",
    "PatientProfile",
    "MedicalState",
    "ConversationState",
    "WorkerState",
]
