# ============= LangGraph Agent Orchestrator =============
import logging
import json
import re
import datetime
from typing import Dict, List, Optional, Any, Literal, TypedDict, Annotated
from dataclasses import dataclass, asdict
import operator

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
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
    RoutingConfig,
    MessageTemplates,
    LoggingConstants,
)
from Utils.output_processors import OutputProcessors
from Utils.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

# ============= State Definitions =============


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


class RiskAssessment(BaseModel):
    """Risk assessment result"""

    severity: Literal["low", "medium", "high", "critical"]
    reasons: List[str]
    action_required: str
    confidence: float = Field(ge=0.0, le=1.0)
    emergency: bool = False


class Visit(BaseModel):
    """ANC visit information"""

    week: int
    date: str
    type: str
    priority: str
    notes: str


class ANCSchedule(BaseModel):
    """Complete ANC schedule"""

    visits: List[Visit]
    next_visit: Optional[Visit] = None
    summary: Optional[str] = None


class GraphState(TypedDict):
    """Main state for the LangGraph workflow"""

    # Input
    user_input: str
    intent: Optional[str]

    # Patient data
    profile: Optional[PatientProfile]
    medical_state: Optional[MedicalState]

    # Processing results
    risk_assessment: Optional[RiskAssessment]
    schedule: Optional[ANCSchedule]
    nutrition_advice: Optional[str]
    health_answer: Optional[str]
    postpartum_plan: Optional[str]

    # System
    messages: List[BaseMessage]
    error: Optional[str]
    final_response: str


# ============= Enhanced Context Manager =============


class LangGraphPatientContextManager:
    """Enhanced context manager using LangGraph state"""

    def __init__(self):
        self.state: GraphState = {
            "user_input": "",
            "intent": None,
            "profile": None,
            "medical_state": None,
            "risk_assessment": None,
            "schedule": None,
            "nutrition_advice": None,
            "health_answer": None,
            "postpartum_plan": None,
            "messages": [],
            "error": None,
            "final_response": "",
        }
        self.history: List[Dict[str, Any]] = []

    def set_profile(self, profile_data: Dict[str, Any]) -> None:
        """Set patient profile and calculate medical state"""
        try:
            self.state["profile"] = PatientProfile(**profile_data)
            self._update_medical_state()
        except Exception as e:
            logger.error(LoggingConstants.PROFILE_ERROR_LOG.format(error=e))
            # Set basic profile with defaults
            self.state["profile"] = PatientProfile(
                age=profile_data.get("age", MedicalConstants.DEFAULT_PATIENT_AGE),
                lmp_date=profile_data.get("lmp_date", DefaultValues.UNKNOWN_LMP),
                medical_history=profile_data.get(
                    "medical_history", DefaultValues.NOT_SPECIFIED
                ),
            )

    def _update_medical_state(self):
        """Calculate current medical state based on profile"""
        if (
            not self.state["profile"]
            or self.state["profile"].lmp_date == DefaultValues.UNKNOWN_LMP
        ):
            return

        try:
            lmp = datetime.datetime.strptime(
                self.state["profile"].lmp_date, ValidationRules.DATE_FORMAT
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

            # Calculate due date (280 days from LMP)
            due_date = (
                lmp + datetime.timedelta(days=MedicalConstants.PREGNANCY_DURATION_DAYS)
            ).strftime(ValidationRules.DATE_FORMAT)

            self.state["medical_state"] = MedicalState(
                current_week=current_week, trimester=trimester, due_date=due_date
            )
        except ValueError as e:
            logger.error(LoggingConstants.MEDICAL_STATE_ERROR_LOG.format(error=e))
            self.state["medical_state"] = MedicalState()

    def get_context_summary(self, current_input: str = "") -> str:
        """Get formatted context summary"""
        if not self.state["profile"]:
            return "No patient profile available"

        profile = self.state["profile"]
        medical = self.state["medical_state"] or MedicalState()

        return ContextTemplates.PROFILE_SUMMARY.format(
            age=profile.age,
            current_week=medical.current_week,
            trimester=medical.trimester,
            medical_history=profile.medical_history,
            current_input=current_input[:100],
        ).strip()

    def add_interaction(self, user_input: str, response: str, metadata: Dict = None):
        """Add interaction to history"""
        interaction = {
            "user_input": user_input,
            "response": response,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.history.append(interaction)

        # Keep only recent history
        if len(self.history) > DefaultValues.MAX_HISTORY_LENGTH:
            self.history = self.history[-DefaultValues.KEEP_RECENT_HISTORY :]


# ============= Node Functions =============


def classify_intent(state: GraphState) -> GraphState:
    """Classify user intent to determine workflow path"""
    user_input = state["user_input"].lower()

    # Emergency detection - highest priority
    if any(k in user_input for k in IntentKeywords.EMERGENCY_KEYWORDS):
        intent = IntentTypes.EMERGENCY
        # Try to classify emergency type
        if any(k in user_input for k in IntentKeywords.BLEEDING_KEYWORDS):
            state["emergency_type"] = EmergencyConfig.Types.BLEEDING
        elif any(k in user_input for k in IntentKeywords.PAIN_KEYWORDS):
            state["emergency_type"] = EmergencyConfig.Types.PAIN
        elif any(k in user_input for k in IntentKeywords.BREATHING_KEYWORDS):
            state["emergency_type"] = EmergencyConfig.Types.BREATHING
        elif any(k in user_input for k in IntentKeywords.PRESSURE_KEYWORDS):
            state["emergency_type"] = EmergencyConfig.Types.PRESSURE
        else:
            state["emergency_type"] = EmergencyConfig.Types.GENERAL
    # Regular intent classification - prioritize specific domains first
    elif any(k in user_input for k in IntentKeywords.POSTPARTUM_KEYWORDS):
        intent = IntentTypes.POSTPARTUM
    elif any(k in user_input for k in IntentKeywords.NUTRITION_KEYWORDS):
        intent = IntentTypes.NUTRITION
    elif any(k in user_input for k in IntentKeywords.PROFILE_KEYWORDS):
        intent = IntentTypes.PROFILE
    elif any(k in user_input for k in IntentKeywords.SCHEDULING_KEYWORDS):
        intent = IntentTypes.SCHEDULING
    else:
        # Route all other queries (including symptoms, feelings, concerns) to health agent
        intent = IntentTypes.HEALTH_QUERY

    state["intent"] = intent
    state["messages"].append(HumanMessage(content=state["user_input"]))

    logger.info(LoggingConstants.INTENT_CLASSIFIED.format(intent=intent))
    logger.info(LoggingConstants.USER_INPUT_LOG.format(user_input=user_input))
    return state


def handle_health_query(state: GraphState) -> GraphState:
    """Handle health queries with conversational, empathetic responses"""
    try:
        logger.info(LoggingConstants.HANDLING_HEALTH_QUERY)

        # Build patient context for personalized responses
        context = ""
        if state["profile"]:
            medical = state["medical_state"] or MedicalState()
            context = ContextTemplates.PATIENT_CONTEXT_FULL.format(
                age=state["profile"].age,
                current_week=medical.current_week,
                trimester=medical.trimester,
                medical_history=state["profile"].medical_history,
                risk_level=medical.risk_level,
            )
        else:
            context = ContextTemplates.NO_PROFILE_CONTEXT

        # Create conversational health prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.CONVERSATIONAL_HEALTH_AGENT),
                ("human", MessageTemplates.HEALTH_HUMAN_MESSAGE),
            ]
        )

        # Generate conversational response
        chain = prompt | langgraph_llm
        result = chain.invoke({"user_input": state["user_input"], "context": context})

        # Clean the response to remove any reasoning text
        cleaned_content = OutputProcessors.clean_all_llm_responses(result.content)

        # Set response
        state["health_answer"] = cleaned_content
        state["final_response"] = cleaned_content
        state["messages"].append(AIMessage(content=cleaned_content))

    except Exception as e:
        logger.error(LoggingConstants.HEALTH_QUERY_ERROR_LOG.format(error=e))
        state["error"] = str(e)
        state["final_response"] = ResponseTemplates.EMOTIONAL_SUPPORT

    return state


def provide_nutrition_advice(state: GraphState) -> GraphState:
    """Provide nutrition advice using specialized agent"""
    try:
        logger.info(LoggingConstants.PROVIDING_NUTRITION_ADVICE)

        # Build patient context for personalized advice
        context = ""
        if state["profile"]:
            medical = state["medical_state"] or MedicalState()
            allergies_text = (
                ", ".join(state["profile"].allergies)
                if state["profile"].allergies
                else DefaultValues.NONE_REPORTED
            )
            context = ContextTemplates.PATIENT_CONTEXT_WITH_ALLERGIES.format(
                age=state["profile"].age,
                current_week=medical.current_week,
                trimester=medical.trimester,
                medical_history=state["profile"].medical_history,
                allergies=allergies_text,
            )
        else:
            context = ContextTemplates.NO_PROFILE_NUTRITION_CONTEXT

        # Create nutrition prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.NUTRITION_SPECIALIST),
                ("human", MessageTemplates.NUTRITION_HUMAN_MESSAGE),
            ]
        )

        # Generate nutrition advice
        chain = prompt | langgraph_llm
        result = chain.invoke({"user_input": state["user_input"], "context": context})

        # Clean and structure the response
        medical = state["medical_state"] or MedicalState()
        current_week = medical.current_week

        # Apply output cleaning and structuring
        cleaned_content = OutputProcessors.clean_nutrition_response(result.content)
        structured_content = OutputProcessors.enforce_nutrition_structure(
            cleaned_content, current_week
        )

        # Set response
        state["nutrition_advice"] = structured_content
        state["final_response"] = structured_content
        state["messages"].append(AIMessage(content=structured_content))

    except Exception as e:
        logger.error(LoggingConstants.NUTRITION_ERROR_LOG.format(error=e))
        state["error"] = str(e)
        state["final_response"] = ResponseTemplates.NUTRITION_ERROR

    return state


def generate_schedule(state: GraphState) -> GraphState:
    """Generate ANC schedule using specialized agent"""
    try:
        logger.info(LoggingConstants.GENERATING_SCHEDULE)

        if not state["medical_state"]:
            logger.warning(LoggingConstants.NO_MEDICAL_STATE_WARNING)
            state["final_response"] = ResponseTemplates.NO_PROFILE_ERROR
            return state

        current_week = state["medical_state"].current_week
        logger.info(LoggingConstants.CURRENT_WEEK_LOG.format(current_week=current_week))

        # Create scheduling prompt with stronger format enforcement
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.SCHEDULE_COORDINATOR),
                ("human", MessageTemplates.SCHEDULE_HUMAN_MESSAGE),
            ]
        )

        # Generate schedule with enhanced error handling
        try:
            chain = prompt | langgraph_llm
            llm_result = chain.invoke(
                {
                    "current_week": current_week,
                    "due_date": state["medical_state"].due_date or "unknown",
                }
            )

            # Extract JSON from response
            response_text = llm_result.content.strip()
            logger.info(f"Raw LLM response: {response_text[:200]}...")

            # Try to extract JSON from response (handle cases where LLM adds extra text)
            try:
                # First try direct parsing
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON within the response
                json_start = response_text.find(ValidationRules.JSON_START_CHAR)
                json_end = response_text.rfind(ValidationRules.JSON_END_CHAR) + 1

                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    logger.info(f"Extracted JSON: {json_text}")
                    try:
                        result = json.loads(json_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON extraction failed: {e}, Text: {json_text}")
                        result = {
                            "visits": [],
                            "summary": "Generated fallback schedule",
                        }
                else:
                    logger.error(f"No JSON found in response: {response_text}")
                    result = {"visits": [], "summary": "Generated fallback schedule"}

        except Exception as e:
            logger.error(f"LLM invocation error: {e}")
            result = {"visits": [], "summary": "Generated fallback schedule"}

        # Create schedule object with robust error handling
        visits = []
        base_date = datetime.datetime.now()

        for i, visit_data in enumerate(result.get("visits", [])):
            try:
                # Validate all required fields are present
                missing_fields = [
                    field
                    for field in ValidationRules.VISIT_REQUIRED_FIELDS
                    if field not in visit_data
                ]

                if missing_fields:
                    logger.warning(
                        f"Visit data missing fields {missing_fields}: {visit_data}"
                    )
                    # Create complete visit with defaults
                    visit_week = visit_data.get("week", current_week + (i + 1) * 4)
                    visit_dict = {
                        "week": visit_week,
                        "date": visit_data.get(
                            "date",
                            (
                                base_date
                                + datetime.timedelta(weeks=visit_week - current_week)
                            ).strftime(ValidationRules.DATE_FORMAT),
                        ),
                        "type": visit_data.get(
                            "type", DefaultValues.DEFAULT_VISIT_TYPE
                        ),
                        "priority": visit_data.get(
                            "priority", DefaultValues.DEFAULT_PRIORITY
                        ),
                        "notes": visit_data.get(
                            "notes", f"Standard ANC visit at week {visit_week}"
                        ),
                    }
                else:
                    visit_dict = visit_data

                # Validate and create Visit object
                visits.append(Visit(**visit_dict))
                logger.info(f"Created visit: week {visit_dict['week']}")

            except Exception as e:
                logger.error(f"Error creating visit from {visit_data}: {e}")
                # Create a safe default visit
                default_week = current_week + (i + 1) * 4
                if (
                    default_week <= MedicalConstants.MAX_PREGNANCY_WEEKS
                ):  # Don't schedule beyond 40 weeks
                    visits.append(
                        Visit(
                            week=default_week,
                            date=(
                                base_date
                                + datetime.timedelta(weeks=default_week - current_week)
                            ).strftime(ValidationRules.DATE_FORMAT),
                            type=DefaultValues.DEFAULT_VISIT_TYPE,
                            priority=DefaultValues.DEFAULT_PRIORITY,
                            notes=f"Standard ANC visit at week {default_week}",
                        )
                    )

        # Filter future visits only
        future_visits = [v for v in visits if v.week > current_week]

        if not future_visits:
            # Generate fallback schedule
            future_visits = _generate_fallback_visits(current_week)

        schedule = ANCSchedule(
            visits=future_visits,
            next_visit=future_visits[0] if future_visits else None,
            summary=result.get("summary", "Personalized ANC schedule"),
        )

        state["schedule"] = schedule

        # Generate response
        response = ResponseTemplates.SCHEDULE_HEADER.format(current_week=current_week)

        for i, visit in enumerate(future_visits[:4], 1):
            response += ResponseTemplates.SCHEDULE_VISIT_TEMPLATE.format(
                index=i,
                week=visit.week,
                date=visit.date,
                visit_type=visit.type.title(),
                priority=visit.priority.title(),
                notes=visit.notes,
            )

        if schedule.next_visit:
            response += ResponseTemplates.SCHEDULE_NEXT_VISIT.format(
                week=schedule.next_visit.week, date=schedule.next_visit.date
            )

        state["final_response"] = response
        state["messages"].append(AIMessage(content=response))

    except Exception as e:
        logger.error(LoggingConstants.SCHEDULE_ERROR_LOG.format(error=e))
        state["error"] = str(e)
        state["final_response"] = ResponseTemplates.SCHEDULE_ERROR

    return state


def handle_emergency(state: GraphState) -> GraphState:
    """Handle emergency situations with immediate alert and guidance"""
    try:
        logger.info(LoggingConstants.PROCESSING_EMERGENCY)

        emergency_type = state.get("emergency_type", EmergencyConfig.Types.GENERAL)

        # Create emergency response prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.EMERGENCY_SPECIALIST),
                ("human", MessageTemplates.EMERGENCY_HUMAN_MESSAGE),
            ]
        )

        # Get context
        context = ""
        if state["profile"] and state["medical_state"]:
            context = ContextTemplates.PATIENT_CONTEXT_EMERGENCY.format(
                age=state["profile"].age,
                current_week=state["medical_state"].current_week,
                trimester=state["medical_state"].trimester,
            )
            if state["profile"].medical_history:
                context += f", History: {state['profile'].medical_history}"

        # Generate emergency response
        chain = prompt | langgraph_llm
        result = chain.invoke(
            {
                "emergency_type": emergency_type,
                "context": context,
                "question": state["user_input"],
            }
        )

        # Clean the emergency response
        cleaned_emergency_content = OutputProcessors.clean_all_llm_responses(
            result.content
        )

        # Format emergency response using constants
        emergency_number = EmergencyConfig.BANGLADESH_EMERGENCY
        emergency_response = f"""{EmergencyConfig.EMERGENCY_ALERT_HEADER}

{cleaned_emergency_content}

{EmergencyConfig.ALERT_STATUS_TEMPLATE}

{EmergencyConfig.IMMEDIATE_ACTIONS_TEMPLATE.format(emergency_number=emergency_number)}

{EmergencyConfig.EMERGENCY_HOTLINES_TEMPLATE.format(
    emergency_number=emergency_number,
    maternal_hotline=EmergencyConfig.MATERNAL_HOTLINE
)}

{EmergencyConfig.WARNING_FOOTER}"""

        state["emergency_response"] = cleaned_emergency_content
        state["final_response"] = emergency_response
        state["messages"].append(AIMessage(content=emergency_response))

        # Mark as emergency handled
        state["emergency_handled"] = True

    except Exception as e:
        logger.error(LoggingConstants.EMERGENCY_ERROR_LOG.format(error=e))
        state["error"] = str(e)
        state["final_response"] = EmergencyConfig.SYSTEM_EMERGENCY_RESPONSE
        state["emergency_handled"] = True

    return state


def generate_postpartum_plan(state: GraphState) -> GraphState:
    """Generate postpartum care plan"""
    try:
        logger.info(LoggingConstants.GENERATING_POSTPARTUM_PLAN)

        # Create postpartum prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SystemPrompts.POSTPARTUM_COORDINATOR),
                ("human", MessageTemplates.POSTPARTUM_HUMAN_MESSAGE),
            ]
        )

        # Get context
        context = ""
        if state["profile"]:
            context = f"Age: {state['profile'].age}, Medical history: {state['profile'].medical_history}"

        # Generate plan
        chain = prompt | langgraph_llm
        result = chain.invoke({"context": context})

        # Clean the postpartum response
        cleaned_postpartum_content = OutputProcessors.clean_all_llm_responses(
            result.content
        )

        state["postpartum_plan"] = cleaned_postpartum_content
        state["final_response"] = (
            f"🏥 **Postpartum Care Plan**\n\n{cleaned_postpartum_content}"
        )
        state["messages"].append(AIMessage(content=state["final_response"]))

    except Exception as e:
        logger.error(LoggingConstants.POSTPARTUM_ERROR_LOG.format(error=e))
        state["error"] = str(e)
        state["final_response"] = ResponseTemplates.POSTPARTUM_ERROR

    return state


def show_profile(state: GraphState) -> GraphState:
    """Display patient profile information"""
    if not state["profile"]:
        state["final_response"] = ResponseTemplates.PROFILE_NO_PROFILE
        return state

    profile = state["profile"]
    medical = state["medical_state"] or MedicalState()

    allergies_text = (
        ", ".join(profile.allergies)
        if profile.allergies
        else DefaultValues.NONE_REPORTED
    )
    medications_text = (
        ", ".join(profile.medications)
        if profile.medications
        else DefaultValues.NONE_REPORTED
    )

    response = ResponseTemplates.PROFILE_TEMPLATE.format(
        age=profile.age,
        lmp_date=profile.lmp_date,
        current_week=medical.current_week,
        trimester=medical.trimester,
        medical_history=profile.medical_history,
        allergies=allergies_text,
        medications=medications_text,
    )

    if medical.due_date:
        response += f"\n**Estimated Due Date:** {medical.due_date}"

    state["final_response"] = response
    state["messages"].append(AIMessage(content=response))
    return state


def handle_error(state: GraphState) -> GraphState:
    """Handle any errors that occurred during processing"""
    error_msg = state.get("error", "Unknown error occurred")
    logger.error(f"Handling error: {error_msg}")

    state["final_response"] = ResponseTemplates.GENERIC_ERROR
    state["messages"].append(AIMessage(content=state["final_response"]))
    return state


# ============= Helper Functions =============


def _generate_fallback_visits(current_week: int) -> List[Visit]:
    """Generate fallback visit schedule"""
    base_date = datetime.datetime.now()
    visits = []

    for week in MedicalConstants.STANDARD_ANC_WEEKS:
        if week > current_week:
            days_ahead = (week - current_week) * 7
            visit_date = (base_date + datetime.timedelta(days=days_ahead)).strftime(
                ValidationRules.DATE_FORMAT
            )

            priority = (
                MedicalConstants.PriorityLevels.HIGH
                if week >= 36
                else MedicalConstants.PriorityLevels.MEDIUM
            )

            visits.append(
                Visit(
                    week=week,
                    date=visit_date,
                    type=MedicalConstants.VisitTypes.ROUTINE,
                    priority=priority,
                    notes=f"Standard ANC visit at {week} weeks",
                )
            )

    return visits


# ============= Conditional Edge Functions =============


def route_by_intent(state: GraphState) -> str:
    """Route to appropriate node based on classified intent"""
    intent = state.get("intent")
    return RoutingConfig.INTENT_TO_NODE_MAP.get(intent, RoutingConfig.DEFAULT_ROUTE)


def check_for_errors(state: GraphState) -> str:
    """Check if there were any errors during processing"""
    if state.get("error"):
        return "error_handler"
    return END


# ============= Main LangGraph Workflow =============


class MaatriCareLangGraphOrchestrator:
    """Main orchestrator using LangGraph"""

    def __init__(self):
        # Ensure logging is initialized if not already done
        try:
            # Try to get the root logger and check if it has handlers
            root_logger = logging.getLogger()
            if not root_logger.handlers:
                # If no handlers, initialize logging
                from Utils.logging_config import setup_logging

                setup_logging()
                logger.info("🔧 Logging initialized by MaatriCareLangGraphOrchestrator")
        except Exception as e:
            # Fallback to basic logging if our custom setup fails
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logger.warning(f"⚠️  Fell back to basic logging: {e}")

        self.context_manager = LangGraphPatientContextManager()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Create the state graph
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("classify_intent", classify_intent)
        workflow.add_node("scheduling", generate_schedule)
        workflow.add_node("nutrition", provide_nutrition_advice)
        workflow.add_node("health_query", handle_health_query)
        workflow.add_node("postpartum", generate_postpartum_plan)
        workflow.add_node("profile", show_profile)
        workflow.add_node("emergency", handle_emergency)
        workflow.add_node("error_handler", handle_error)

        # Set entry point
        workflow.set_entry_point("classify_intent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "classify_intent",
            route_by_intent,
            RoutingConfig.INTENT_TO_NODE_MAP,
        )

        # Add edges to end
        workflow.add_conditional_edges(
            "emergency", check_for_errors, {"error_handler": "error_handler", END: END}
        )

        workflow.add_conditional_edges(
            "scheduling", check_for_errors, {"error_handler": "error_handler", END: END}
        )

        workflow.add_conditional_edges(
            "nutrition", check_for_errors, {"error_handler": "error_handler", END: END}
        )

        workflow.add_conditional_edges(
            "health_query",
            check_for_errors,
            {"error_handler": "error_handler", END: END},
        )

        workflow.add_conditional_edges(
            "postpartum", check_for_errors, {"error_handler": "error_handler", END: END}
        )

        workflow.add_conditional_edges(
            "profile", check_for_errors, {"error_handler": "error_handler", END: END}
        )

        workflow.add_edge("error_handler", END)

        # Compile the workflow
        return workflow.compile(checkpointer=MemorySaver())

    def process_query(
        self, user_input: str, profile_data: Dict[str, Any] = None
    ) -> str:
        """Process user query through the LangGraph workflow"""

        # Initialize state
        initial_state: GraphState = {
            "user_input": user_input,
            "intent": None,
            "profile": None,
            "medical_state": None,
            "risk_assessment": None,
            "schedule": None,
            "nutrition_advice": None,
            "health_answer": None,
            "postpartum_plan": None,
            "messages": [],
            "error": None,
            "final_response": "",
        }

        # Set profile if provided
        if profile_data:
            try:
                initial_state["profile"] = PatientProfile(**profile_data)
                # Calculate medical state
                if initial_state["profile"].lmp_date != DefaultValues.UNKNOWN_LMP:
                    lmp = datetime.datetime.strptime(
                        initial_state["profile"].lmp_date, ValidationRules.DATE_FORMAT
                    )
                    today = datetime.datetime.now()
                    days_pregnant = (today - lmp).days
                    current_week = days_pregnant // 7

                    if current_week <= MedicalConstants.FIRST_TRIMESTER_END:
                        trimester = 1
                    elif current_week <= MedicalConstants.SECOND_TRIMESTER_END:
                        trimester = 2
                    else:
                        trimester = 3

                    due_date = (
                        lmp
                        + datetime.timedelta(
                            days=MedicalConstants.PREGNANCY_DURATION_DAYS
                        )
                    ).strftime(ValidationRules.DATE_FORMAT)

                    initial_state["medical_state"] = MedicalState(
                        current_week=current_week,
                        trimester=trimester,
                        due_date=due_date,
                    )
            except Exception as e:
                logger.error(LoggingConstants.PROFILE_ERROR_LOG.format(error=e))
        elif self.context_manager.state["profile"]:
            # Try to use existing context
            initial_state["profile"] = self.context_manager.state["profile"]
            initial_state["medical_state"] = self.context_manager.state["medical_state"]
            logger.info(
                LoggingConstants.PROFILE_USAGE_LOG.format(
                    age=initial_state["profile"].age
                )
            )

        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": "main_thread"}}
            result = self.workflow.invoke(initial_state, config)

            # Update context manager
            self.context_manager.state.update(result)
            self.context_manager.add_interaction(
                user_input, result["final_response"], {"intent": result.get("intent")}
            )

            return result["final_response"]

        except Exception as e:
            logger.error(LoggingConstants.WORKFLOW_ERROR_LOG.format(error=e))
            return ResponseTemplates.GENERIC_ERROR

    def set_profile(self, profile_data: Dict[str, Any]) -> None:
        """Set patient profile in context manager"""
        self.context_manager.set_profile(profile_data)

    def get_context_manager(self) -> LangGraphPatientContextManager:
        """Get the context manager instance"""
        return self.context_manager


# Maintain the original PatientContextManager class name for compatibility
PatientContextManager = LangGraphPatientContextManager

# ============= Export Main Orchestrator =============
__all__ = [
    "MaatriCareLangGraphOrchestrator",
    "LangGraphPatientContextManager",
    "PatientContextManager",
]
