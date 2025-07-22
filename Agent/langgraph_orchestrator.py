# ============= MaatriCare LangGraph Native Orchestrator =============
"""
LangGraph-native implementation using create_react_agent and proper tool orchestration.
This addresses the conversational flow issues and uses LangGraph's built-in capabilities.
"""

import logging
import datetime
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from dataclasses import dataclass
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
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


@dataclass
class AgentContext:
    """Shared context for all agents"""

    user_input: str
    patient_profile: Optional[PatientProfile] = None
    medical_state: Optional[MedicalState] = None
    conversation_history: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.metadata is None:
            self.metadata = {}

    def get_context_summary(self) -> str:
        """Get formatted context summary for agents"""
        if not self.patient_profile:
            return "No patient profile available - provide general pregnancy guidance"

        return ContextTemplates.PATIENT_CONTEXT_FULL.format(
            age=self.patient_profile.age,
            current_week=self.medical_state.current_week if self.medical_state else 0,
            trimester=self.medical_state.trimester if self.medical_state else 1,
            medical_history=self.patient_profile.medical_history,
            risk_level=self.medical_state.risk_level if self.medical_state else "low",
        )


class PatientContextManager:
    """Manages patient context and conversation history"""

    def __init__(self):
        self.current_context: Optional[AgentContext] = None
        self.conversation_history: List[Dict[str, Any]] = []
        self.logger = get_logger("MaatriCare.ContextManager")

    @property
    def state(self) -> Dict[str, Any]:
        """Property to access current state as a dictionary for UI compatibility"""
        state_dict = {}

        if self.current_context and self.current_context.patient_profile:
            state_dict["profile"] = self.current_context.patient_profile

        if self.current_context and self.current_context.medical_state:
            state_dict["medical_state"] = self.current_context.medical_state

        return state_dict

    def set_profile(self, profile_data: Dict[str, Any]) -> None:
        """Set patient profile and calculate medical state"""
        try:
            profile = PatientProfile(**profile_data)
            medical_state = self._calculate_medical_state(profile)

            if self.current_context:
                self.current_context.patient_profile = profile
                self.current_context.medical_state = medical_state
            else:
                self.current_context = AgentContext(
                    user_input="",
                    patient_profile=profile,
                    medical_state=medical_state,
                    conversation_history=self.conversation_history.copy(),
                )

            self.logger.info(
                f"Profile set: Age {profile.age}, Week {medical_state.current_week}"
            )

        except Exception as e:
            self.logger.error(f"Error setting profile: {e}")
            if not self.current_context:
                self.current_context = AgentContext(user_input="")

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

    def create_context(self, user_input: str) -> AgentContext:
        """Create context for current user input"""
        if self.current_context:
            context = AgentContext(
                user_input=user_input,
                patient_profile=self.current_context.patient_profile,
                medical_state=self.current_context.medical_state,
                conversation_history=self.conversation_history.copy(),
            )
        else:
            context = AgentContext(
                user_input=user_input,
                conversation_history=self.conversation_history.copy(),
            )
        return context

    def add_interaction(self, user_input: str, response: str, metadata: Dict = None):
        """Add interaction to history"""
        interaction = {
            "user_input": user_input,
            "response": response,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.conversation_history.append(interaction)

        # Keep only recent history
        if len(self.conversation_history) > DefaultValues.MAX_HISTORY_LENGTH:
            self.conversation_history = self.conversation_history[
                -DefaultValues.KEEP_RECENT_HISTORY :
            ]


# ============= Conversation State =============


class ConversationState(TypedDict):
    """State for the conversation graph"""

    messages: Annotated[List[BaseMessage], "The conversation messages"]
    patient_profile: Optional[Dict[str, Any]]
    medical_state: Optional[Dict[str, Any]]
    current_intent: Optional[str]


# ============= LangGraph Tools =============


@tool
def assess_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Assess the user's intent and determine if specialist agents are needed.
    Returns intent classification and whether to engage conversationally first.
    """
    user_lower = user_input.lower()

    # Immediate emergency check
    if any(keyword in user_lower for keyword in IntentKeywords.EMERGENCY_KEYWORDS):
        return {
            "primary_intent": "emergency",
            "needs_conversation": False,
            "urgency": "high",
            "reasoning": "Emergency situation detected - immediate specialist response needed",
        }

    # Check for emotional distress
    mood_keywords = [
        "feel",
        "feeling",
        "sad",
        "depressed",
        "anxious",
        "worried",
        "scared",
        "upset",
        "cry",
        "not eating",
        "don't feel like",
    ]
    if any(keyword in user_lower for keyword in mood_keywords):
        return {
            "primary_intent": "emotional_health",
            "needs_conversation": True,
            "urgency": "medium",
            "reasoning": "Emotional state detected - needs empathetic conversation first",
        }

    # Check for specific specialist keywords
    specialist_mappings = {
        "nutrition": IntentKeywords.NUTRITION_KEYWORDS,
        "exercise": IntentKeywords.EXERCISE_KEYWORDS,
        "scheduling": IntentKeywords.SCHEDULING_KEYWORDS,
        "postpartum": IntentKeywords.POSTPARTUM_KEYWORDS,
    }

    for specialist, keywords in specialist_mappings.items():
        if any(keyword in user_lower for keyword in keywords):
            return {
                "primary_intent": specialist,
                "needs_conversation": True,
                "urgency": "low",
                "reasoning": f"Specialist topic detected but needs conversational engagement first",
            }

    # Default: conversational health
    return {
        "primary_intent": "general_health",
        "needs_conversation": True,
        "urgency": "low",
        "reasoning": "General health query - conversational approach appropriate",
    }


@tool
def emergency_response_tool(emergency_type: str, context: str) -> str:
    """Handle emergency situations with immediate response"""
    try:
        logger.warning(f"EMERGENCY: {emergency_type}")

        # Create emergency prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.EMERGENCY_SPECIALIST),
                (
                    "human",
                    "Emergency type: {emergency_type}\nContext: {context}\nProvide immediate guidance.",
                ),
            ]
        )

        chain = prompt | langgraph_llm
        result = chain.invoke({"emergency_type": emergency_type, "context": context})

        # Format with emergency headers
        emergency_number = EmergencyConfig.BANGLADESH_EMERGENCY

        return f"""{EmergencyConfig.EMERGENCY_ALERT_HEADER}

{OutputProcessors.clean_all_llm_responses(result.content)}

{EmergencyConfig.IMMEDIATE_ACTIONS_TEMPLATE.format(emergency_number=emergency_number)}

{EmergencyConfig.EMERGENCY_HOTLINES_TEMPLATE.format(
    emergency_number=emergency_number,
    maternal_hotline=EmergencyConfig.MATERNAL_HOTLINE
)}"""

    except Exception as e:
        logger.error(f"Error in emergency tool: {e}")
        return EmergencyConfig.SYSTEM_EMERGENCY_RESPONSE


@tool
def nutrition_specialist_tool(query: str, context: str) -> str:
    """Provide specialized nutrition guidance"""
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.NUTRITION_SPECIALIST),
                ("human", MessageTemplates.NUTRITION_HUMAN_MESSAGE),
            ]
        )

        chain = prompt | langgraph_llm
        result = chain.invoke({"user_input": query, "context": context})

        return OutputProcessors.clean_all_llm_responses(result.content)

    except Exception as e:
        logger.error(f"Error in nutrition tool: {e}")
        return "I apologize, but I'm having trouble accessing nutrition information right now. Please try again."


@tool
def mood_support_tool(query: str, context: str) -> str:
    """Provide emotional support with video recommendations"""
    try:
        # Get mood support videos
        videos = youtube_service.search_mood_support_videos()
        video_links = youtube_service.format_videos_for_llm(videos)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.MOOD_SUPPORT_SPECIALIST),
                ("human", MessageTemplates.MOOD_SUPPORT_HUMAN_MESSAGE),
            ]
        )

        chain = prompt | langgraph_llm
        result = chain.invoke(
            {"user_input": query, "context": context, "youtube_links": video_links}
        )

        return OutputProcessors.clean_all_llm_responses(result.content)

    except Exception as e:
        logger.error(f"Error in mood support tool: {e}")
        return ResponseTemplates.EMOTIONAL_SUPPORT


@tool
def exercise_guidance_tool(query: str, context: str, trimester: int = 2) -> str:
    """Provide exercise guidance with video recommendations"""
    try:
        videos = youtube_service.search_exercise_videos(trimester, trimester * 13)
        video_links = youtube_service.format_videos_for_llm(videos)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.EXERCISE_SPECIALIST),
                ("human", MessageTemplates.EXERCISE_HUMAN_MESSAGE),
            ]
        )

        chain = prompt | langgraph_llm
        result = chain.invoke(
            {"user_input": query, "context": context, "youtube_links": video_links}
        )

        return OutputProcessors.clean_all_llm_responses(result.content)

    except Exception as e:
        logger.error(f"Error in exercise tool: {e}")
        return "I apologize, but I'm having trouble accessing exercise information right now."


@tool
def scheduling_tool(current_week: int, context: str) -> str:
    """Generate ANC scheduling information"""
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    SystemPrompts.SCHEDULE_COORDINATOR.format(
                        current_week=current_week
                    ),
                ),
                ("human", MessageTemplates.SCHEDULE_HUMAN_MESSAGE),
            ]
        )

        chain = prompt | langgraph_llm
        result = chain.invoke({"current_week": current_week, "due_date": "unknown"})

        return OutputProcessors.clean_all_llm_responses(result.content)

    except Exception as e:
        logger.error(f"Error in scheduling tool: {e}")
        return "I apologize, but I'm having trouble accessing scheduling information right now."


# ============= Main LangGraph Native Orchestrator =============


class MaatriCareLangGraphNativeOrchestrator:
    """
    LangGraph-native orchestrator that emphasizes conversational flow
    before engaging specialist agents when appropriate.
    """

    def __init__(self):
        self.logger = get_logger("MaatriCare.LangGraphNative")
        self.context_manager = PatientContextManager()

        # Available tools for the agent
        self.tools = [
            assess_user_intent,
            emergency_response_tool,
            nutrition_specialist_tool,
            mood_support_tool,
            exercise_guidance_tool,
            scheduling_tool,
        ]

        # Create the main conversational agent
        self.main_agent = self._create_main_agent()

        self.logger.info(
            "Initialized LangGraph Native Orchestrator with conversational flow"
        )

    def _create_main_agent(self):
        """Create the main conversational agent using LangGraph"""

        # Main system prompt that emphasizes conversation
        system_prompt = """You are MaatriCare, a compassionate maternal health assistant specialized in pregnancy care for mothers in Bangladesh.

CONVERSATION PHILOSOPHY:
- ALWAYS respond conversationally and empathetically first
- Ask follow-up questions to understand the user's situation better
- Only use specialist tools when you have enough context and the user really needs specialized help
- For emotional statements like "I don't feel like eating", engage conversationally first - ask about their feelings, when this started, what might be causing it
- Build trust through conversation before providing specialized advice

TOOL USAGE GUIDELINES:
- Use assess_user_intent to understand what the user needs
- For EMERGENCIES (bleeding, severe pain, breathing problems) - use emergency_response_tool immediately
- For emotional distress - provide conversational support first, only use mood_support_tool if needed
- For nutrition topics - engage conversationally first, ask about specific concerns before using nutrition_specialist_tool
- For exercise questions - understand their current activity level before using exercise_guidance_tool

RESPONSE STYLE:
- Be warm, empathetic, and culturally sensitive
- Use simple language accessible to Bengali-speaking mothers
- Ask one question at a time to avoid overwhelming
- Show genuine care and concern
- Provide reassurance when appropriate

Remember: You are a trusted companion in their pregnancy journey. Conversation and understanding come first, specialized tools second."""

        return create_react_agent(
            langgraph_llm,
            self.tools,
            prompt=system_prompt,
        )

    def process_query(
        self,
        user_input: str,
        profile_data: Dict[str, Any] = None,
    ) -> str:
        """
        Process user query with conversational-first approach
        """
        try:
            # Set profile if provided
            if profile_data:
                self.context_manager.set_profile(profile_data)

            # Create context summary for tools
            context = self.context_manager.create_context(user_input)
            context_summary = context.get_context_summary()

            # The agent will use tools as needed based on the conversation
            result = self.main_agent.invoke(
                {"messages": [HumanMessage(content=user_input)]}
            )

            # Get the final message
            if result["messages"]:
                final_response = result["messages"][-1].content
            else:
                final_response = ResponseTemplates.GENERIC_ERROR

            # Add to conversation history
            self.context_manager.add_interaction(user_input, final_response)

            self.logger.info(f"Processed query successfully: {user_input[:50]}...")
            return final_response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return ResponseTemplates.GENERIC_ERROR

    def set_profile(self, profile_data: Dict[str, Any]) -> None:
        """Set patient profile"""
        self.context_manager.set_profile(profile_data)

    def get_context_manager(self) -> PatientContextManager:
        """Get context manager"""
        return self.context_manager


# ============= Exports =============

# Main exports
__all__ = [
    "MaatriCareLangGraphNativeOrchestrator",
    "PatientContextManager",
    "PatientProfile",
    "MedicalState",
    "AgentContext",
    "ConversationState",
    # Tools
    "assess_user_intent",
    "emergency_response_tool",
    "nutrition_specialist_tool",
    "mood_support_tool",
    "exercise_guidance_tool",
    "scheduling_tool",
]
