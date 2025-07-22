import sys
import os
import streamlit as st
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Initialize centralized logging first
try:
    from Utils.logging_config import get_logger, setup_logging

    # Check if logging is already initialized, if not, set it up
    if not logging.getLogger().handlers:
        setup_logging()
    logger = get_logger("MaatriCare.UI")
    logger.info("🖥️  MaatriCare UI Starting Up")
except ImportError as e:
    # Fallback to basic logging if centralized logging is not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Using basic logging as fallback: {e}")

# Import the new LangGraph orchestrator
from Agent.agent_orchestrator import (
    PatientContextManager,
    MaatriCareLangGraphOrchestrator,
)

# Import output processor for cleaning responses
from Utils.output_processors import OutputProcessors


# NEW FEATURE: Enhanced error handling for UI
def handle_ui_error(error: Exception, context: str = "operation") -> str:
    """Handle UI errors gracefully with user-friendly messages"""
    logger.error(f"UI Error in {context}: {str(error)}")

    error_messages_en = {
        "profile_creation": "There was an issue creating your profile. Please check your input and try again.",
        "health_query": "I'm having trouble processing your health question right now. Please try rephrasing or contact your healthcare provider.",
        "risk_assessment": "Unable to complete risk assessment. If you have urgent symptoms, please seek immediate medical care.",
        "scheduling": "Cannot access scheduling system right now. Please contact your clinic directly.",
        "nutrition": "Nutrition advice is temporarily unavailable. Please consult your healthcare provider for dietary guidance.",
        "chat_processing": "I'm having trouble processing your message right now. Please try again or contact support.",
    }

    error_messages_bn = {
        "profile_creation": "আপনার প্রোফাইল তৈরিতে সমস্যা হয়েছে। অনুগ্রহ করে আপনার ইনপুট চেক করুন এবং আবার চেষ্টা করুন।",
        "health_query": "এই মুহূর্তে আপনার স্বাস্থ্য প্রশ্ন প্রক্রিয়া করতে আমার সমস্যা হচ্ছে। অনুগ্রহ করে পুনরায় বলুন বা আপনার স্বাস্থ্যসেবা প্রদানকারীর সাথে যোগাযোগ করুন।",
        "risk_assessment": "ঝুঁকি মূল্যায়ন সম্পূর্ণ করতে অক্ষম। যদি আপনার জরুরি লক্ষণ থাকে, অনুগ্রহ করে অবিলম্বে চিকিৎসা সেবা নিন।",
        "scheduling": "এই মুহূর্তে সময়সূচী সিস্টেম অ্যাক্সেস করতে পারছি না। অনুগ্রহ করে সরাসরি আপনার ক্লিনিকে যোগাযোগ করুন।",
        "nutrition": "পুষ্টি পরামর্শ সাময়িকভাবে অনুপলব্ধ। খাদ্য নির্দেশনার জন্য অনুগ্রহ করে আপনার স্বাস্থ্যসেবা প্রদানকারীর সাথে পরামর্শ করুন।",
        "chat_processing": "এই মুহূর্তে আপনার বার্তা প্রক্রিয়া করতে আমার সমস্যা হচ্ছে। অনুগ্রহ করে আবার চেষ্টা করুন বা সহায়তার জন্য যোগাযোগ করুন।",
    }

    # Get current language from session state, default to English
    current_lang = getattr(st.session_state, "language", "en")
    error_messages = error_messages_bn if current_lang == "bn" else error_messages_en

    default_message = (
        "কিছু ভুল হয়ে গেছে। অনুগ্রহ করে আবার চেষ্টা করুন বা সমস্যা অব্যাহত থাকলে সহায়তার জন্য যোগাযোগ করুন।"
        if current_lang == "bn"
        else "Something went wrong. Please try again or contact support if the problem persists."
    )

    return error_messages.get(context, default_message)


# NEW FEATURE: Enhanced user feedback
def show_loading_message(operation: str):
    """Show appropriate loading message based on operation"""
    loading_messages_en = {
        "profile": "Setting up your personalized maternal care profile...",
        "risk": "Analyzing your symptoms using WHO maternal health guidelines...",
        "schedule": "Calculating your optimal ANC appointment schedule...",
        "nutrition": "Preparing personalized nutrition recommendations...",
        "teleconsult": "Evaluating your teleconsultation needs...",
        "health": "Searching for reliable health information...",
        "response": "Processing your request...",
    }

    loading_messages_bn = {
        "profile": "আপনার ব্যক্তিগতকৃত মাতৃযত্ন প্রোফাইল সেটআপ করা হচ্ছে...",
        "risk": "WHO মাতৃস্বাস্থ্য নির্দেশিকা ব্যবহার করে আপনার লক্ষণ বিশ্লেষণ করা হচ্ছে...",
        "schedule": "আপনার সর্বোত্তম ANC অ্যাপয়েন্টমেন্ট সময়সূচী গণনা করা হচ্ছে...",
        "nutrition": "ব্যক্তিগতকৃত পুষ্টি সুপারিশ প্রস্তুত করা হচ্ছে...",
        "teleconsult": "আপনার টেলিকনসালটেশন প্রয়োজন মূল্যায়ন করা হচ্ছে...",
        "health": "নির্ভরযোগ্য স্বাস্থ্য তথ্য অনুসন্ধান করা হচ্ছে...",
        "response": "আপনার অনুরোধ প্রক্রিয়া করা হচ্ছে...",
    }

    # Get current language from session state, default to English
    current_lang = getattr(st.session_state, "language", "en")
    loading_messages = (
        loading_messages_bn if current_lang == "bn" else loading_messages_en
    )

    return loading_messages.get(
        operation, loading_messages.get("response", "Processing...")
    )


# NEW FEATURE: Weekly development information
def get_weekly_development_info(week: int) -> dict:
    """Get week-specific baby development information"""
    # English version
    weekly_info_en = {
        4: {
            "size": "poppy seed 🌱",
            "development": "Implantation occurs, early placenta begins forming",
            "symptoms": "Light spotting, fatigue, breast tenderness",
        },
        5: {
            "size": "sesame seed 🌱",
            "development": "Heart and circulatory system begin to form",
            "symptoms": "Missed period, nausea, mood swings",
        },
        6: {
            "size": "lentil 🫘",
            "development": "Neural tube closes, early brain and heart activity begin",
            "symptoms": "Morning sickness, frequent urination, fatigue",
        },
        7: {
            "size": "blueberry 🫐",
            "development": "Limb buds form, brain and face continue developing",
            "symptoms": "Food aversions, increased sense of smell",
        },
        8: {
            "size": "raspberry 🫐",
            "development": "Fingers and toes visible, neural connections begin",
            "symptoms": "Nausea, breast changes, mood fluctuations",
        },
        9: {
            "size": "cherry 🍒",
            "development": "All essential organs are beginning to develop",
            "symptoms": "Bloating, fatigue, emotional ups and downs",
        },
        10: {
            "size": "strawberry 🍓",
            "development": "Vital organs functioning, limbs bend, facial features refine",
            "symptoms": "Slight energy improvement, nausea may ease",
        },
        11: {
            "size": "fig 🍈",
            "development": "External genitals begin to form, baby starts swallowing",
            "symptoms": "Possible increase in energy, breast tenderness continues",
        },
        12: {
            "size": "lime 🍈",
            "development": "Reflexes developing, intestines move into abdomen",
            "symptoms": "Nausea subsiding, risk of miscarriage drops",
        },
        13: {
            "size": "plum 🟣",
            "development": "Vocal cords form, bones begin hardening",
            "symptoms": "Second trimester starts, more energy, stable appetite",
        },
        14: {
            "size": "peach 🍑",
            "development": "Facial expressions possible, kidneys produce urine",
            "symptoms": "Appetite returns, 'pregnancy glow'",
        },
        15: {
            "size": "apple 🍎",
            "development": "Scalp pattern forms, baby practices breathing",
            "symptoms": "Mild swelling, nasal congestion possible",
        },
        16: {
            "size": "avocado 🥑",
            "development": "Muscles and bones strengthen, baby may suck thumb",
            "symptoms": "You might feel baby move soon (quickening)",
        },
        20: {
            "size": "banana 🍌",
            "development": "Hearing develops, anatomy scan week",
            "symptoms": "Fetal kicks felt, back pain may start",
        },
        24: {
            "size": "ear of corn 🌽",
            "development": "Lung branches form, skin becoming less transparent",
            "symptoms": "Leg cramps, stretch marks, viability milestone reached",
        },
        28: {
            "size": "eggplant 🍆",
            "development": "Eyes open, brain activity increases",
            "symptoms": "Third trimester starts, shortness of breath may begin",
        },
        32: {
            "size": "coconut 🥥",
            "development": "Bones harden, baby practices breathing",
            "symptoms": "Braxton Hicks contractions, sleep disturbances",
        },
        36: {
            "size": "honeydew melon 🍈",
            "development": "Baby's head may engage in pelvis, body fat increasing",
            "symptoms": "Frequent urination, pelvic pressure",
        },
        40: {
            "size": "watermelon 🍉",
            "development": "Baby fully developed, ready for birth",
            "symptoms": "Signs of labor may begin: contractions, water breaking",
        },
    }

    # Bengali version
    weekly_info_bn = {
        4: {
            "size": "পোস্ত দানা 🌱",
            "development": "ইমপ্ল্যান্টেশন হয়, প্রাথমিক প্লাসেন্টা গঠন শুরু",
            "symptoms": "হালকা রক্তপাত, ক্লান্তি, স্তন ব্যথা",
        },
        5: {
            "size": "তিল 🌱",
            "development": "হৃদয় এবং সংবহন তন্ত্র গঠন শুরু",
            "symptoms": "মাসিক বন্ধ, বমি ভাব, মেজাজের পরিবর্তন",
        },
        6: {
            "size": "মসুর ডাল 🫘",
            "development": "নিউরাল টিউব বন্ধ, মস্তিষ্ক ও হৃদয়ের কার্যকলাপ শুরু",
            "symptoms": "সকালের অসুস্থতা, ঘন ঘন প্রস্রাব, ক্লান্তি",
        },
        7: {
            "size": "ব্লুবেরি 🫐",
            "development": "অঙ্গপ্রত্যঙ্গের কুঁড়ি, মস্তিষ্ক ও মুখের বিকাশ অব্যাহত",
            "symptoms": "খাবারে অনীহা, ঘ্রাণশক্তি বৃদ্ধি",
        },
        8: {
            "size": "রাসবেরি 🫐",
            "development": "হাত পায়ের আঙুল দৃশ্যমান, নিউরাল সংযোগ শুরু",
            "symptoms": "বমি ভাব, স্তনের পরিবর্তন, মেজাজের ওঠানামা",
        },
        9: {
            "size": "চেরি 🍒",
            "development": "সমস্ত প্রয়োজনীয় অঙ্গের বিকাশ শুরু",
            "symptoms": "পেট ফুলে থাকা, ক্লান্তি, আবেগজনিত ওঠানামা",
        },
        10: {
            "size": "স্ট্রবেরি 🍓",
            "development": "গুরুত্বপূর্ণ অঙ্গগুলো কাজ করছে, অঙ্গপ্রত্যঙ্গ বাঁকানো, মুখের আকৃতি পরিষ্কার",
            "symptoms": "সামান্য শক্তি বৃদ্ধি, বমি ভাব কমতে পারে",
        },
        11: {
            "size": "ডুমুর 🍈",
            "development": "বাহ্যিক যৌনাঙ্গ গঠন শুরু, শিশু গিলতে শুরু করে",
            "symptoms": "সম্ভাব্য শক্তি বৃদ্ধি, স্তন ব্যথা অব্যাহত",
        },
        12: {
            "size": "লেবু 🍈",
            "development": "রিফ্লেক্স বিকাশ, অন্ত্র পেটে স্থানান্তর",
            "symptoms": "বমি ভাব কমে যাওয়া, গর্ভপাতের ঝুঁকি হ্রাস",
        },
        13: {
            "size": "আলুবোখারা 🟣",
            "development": "স্বরযন্ত্র গঠন, হাড় শক্ত হওয়া শুরু",
            "symptoms": "দ্বিতীয় ত্রৈমাসিক শুরু, বেশি শক্তি, স্থিতিশীল ক্ষুধা",
        },
        14: {
            "size": "পীচ ফল 🍑",
            "development": "মুখের অভিব্যক্তি সম্ভব, কিডনি প্রস্রাব উৎপাদন",
            "symptoms": "ক্ষুধা ফিরে আসা, 'গর্ভাবস্থার উজ্জ্বলতা'",
        },
        15: {
            "size": "আপেল 🍎",
            "development": "মাথার চুলের প্যাটার্ন গঠন, শিশু শ্বাসের অনুশীলন",
            "symptoms": "হালকা ফোলা, নাক বন্ধ সম্ভব",
        },
        16: {
            "size": "অ্যাভোকাডো 🥑",
            "development": "পেশী ও হাড় শক্তিশালী, শিশু বুড়ো আঙুল চুষতে পারে",
            "symptoms": "শীঘ্রই শিশুর নড়াচড়া অনুভব করতে পারেন",
        },
        20: {
            "size": "কলা 🍌",
            "development": "শ্রবণশক্তি বিকাশ, অ্যানাটমি স্ক্যানের সপ্তাহ",
            "symptoms": "ভ্রূণের লাথি অনুভূত, পিঠে ব্যথা শুরু হতে পারে",
        },
        24: {
            "size": "ভুট্টার মোচা 🌽",
            "development": "ফুসফুসের শাখা গঠন, চামড়া কম স্বচ্ছ",
            "symptoms": "পায়ে খিঁচুনি, স্ট্রেচ মার্ক, জীবনক্ষমতার মাইলফলক",
        },
        28: {
            "size": "বেগুন 🍆",
            "development": "চোখ খোলা, মস্তিষ্কের কার্যকলাপ বৃদ্ধি",
            "symptoms": "তৃতীয় ত্রৈমাসিক শুরু, শ্বাসকষ্ট শুরু হতে পারে",
        },
        32: {
            "size": "নারিকেল 🥥",
            "development": "হাড় শক্ত হওয়া, শিশু শ্বাসের অনুশীলন",
            "symptoms": "ব্র্যাক্সটন হিক্স সংকোচন, ঘুমের ব্যাঘাত",
        },
        36: {
            "size": "হানিডিউ মেলন 🍈",
            "development": "শিশুর মাথা পেলভিসে নিয়োজিত হতে পারে, শরীরের চর্বি বৃদ্ধি",
            "symptoms": "ঘন ঘন প্রস্রাব, পেলভিক চাপ",
        },
        40: {
            "size": "তরমুজ 🍉",
            "development": "শিশু সম্পূর্ণ বিকশিত, জন্মের জন্য প্রস্তুত",
            "symptoms": "প্রসবের লক্ষণ শুরু হতে পারে: সংকোচন, জল ভাঙা",
        },
    }

    # Get current language from session state, default to English
    current_lang = getattr(st.session_state, "language", "en")
    weekly_info = weekly_info_bn if current_lang == "bn" else weekly_info_en

    # Find closest week if exact week not found
    if week in weekly_info:
        return weekly_info[week]

    # Find the closest week that has information
    available_weeks = sorted(weekly_info.keys())
    closest_week = min(available_weeks, key=lambda x: abs(x - week))

    info = weekly_info[closest_week].copy()
    note_text = (
        f"সপ্তাহ {closest_week} এর উপর ভিত্তি করে তথ্য (নিকটতম উপলব্ধ ডেটা)"
        if current_lang == "bn"
        else f"Information based on week {closest_week} (closest available data)"
    )
    info["note"] = note_text

    return info


# --- Dark Theme CSS ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    .main {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 0 20px;
    }
    
    /* Chat messages */
    .chat-container {
        background: #161b22;
        border-radius: 12px;
        margin-bottom: 120px;
        min-height: 400px;
        border: 1px solid #30363d;
    }
    
    .message-container {
        padding: 20px;
        margin: 10px 0;
        display: flex;
        flex-direction: column;
    }
    
    .user-message-container {
        align-items: flex-end;
        text-align: right;
    }
    
    .assistant-message-container {
        align-items: flex-start;
        text-align: left;
        padding: 0px 16px 4px 16px;
        margin: 4px 0;
        max-width: 70%;
        display: block;
    }
    
    .assistant-message-bubble {
        background: #21262d;
        border-radius: 18px 18px 18px 4px;
        border: 1px solid #30363d;
        padding: 12px 16px;
        margin: 4px 0 4px 0;
        max-width: 70%;
        display: block;
    }
    
    .assistant-message-content {
        color: #e6edf3 !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }
    
    .assistant-message-content p {
        margin-bottom: 0.5rem !important;
        color: #e6edf3 !important;
    }
    
    .assistant-message-content strong {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    .assistant-message-content ul {
        margin-left: 1rem !important;
        margin-bottom: 0.5rem !important;
        padding-left: 0 !important;
        list-style-type: disc !important;
    }
    
    .assistant-message-content li {
        margin-bottom: 0.25rem !important;
        color: #e6edf3 !important;
        margin-left: 0 !important;
    }
    
    .assistant-message-content br {
        margin-bottom: 0.5rem !important;
    }
    
    .user-message {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        color: #ffffff;
        padding: 12px 16px;
        margin: 4px 0;
        max-width: 70%;
        font-size: 16px;
        line-height: 1.6;
        border-radius: 18px 18px 4px 18px;
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
        align-self: flex-end;
        margin-left: auto;
    }
    
    .user-label {
        font-weight: 600;
        color: #a855f7;
        font-size: 12px;
        margin-bottom: 4px;
        display: block;
        text-align: right;
    }
    
    .assistant-label {
        font-weight: 600;
        background: linear-gradient(135deg, #ff69b4, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 12px;
        margin-bottom: 4px;
        display: block;
        text-align: left;
    }
    
    /* Chat input styling */
    .stChatInput {
        position: fixed !important;
        bottom: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 40px) !important;
        max-width: 860px !important;
        background: #21262d !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
        border: 1px solid #30363d !important;
        z-index: 1000 !important;
    }
    
    .stChatInput > div {
        border: none !important;
        background: transparent !important;
    }
    
    .stChatInput input {
        background-color: transparent !important;
        color: #e6edf3 !important;
        border: none !important;
        padding: 16px 20px !important;
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stChatInput input:focus {
        box-shadow: none !important;
        border: none !important;
        outline: none !important;
    }
    
    .stChatInput input::placeholder {
        color: #8b949e !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #ff69b4, #ffffff);
        color: #333333;
        border-radius: 12px;
        border: none;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 16px;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 2px 8px rgba(255, 105, 180, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #ff1493, #ffb6c1);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 105, 180, 0.4);
        color: #222222;
    }
    
    /* Language toggle button styling */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: linear-gradient(135deg, #21262d, #30363d) !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #30363d, #3fb950) !important;
        border-color: #3fb950 !important;
        transform: translateY(-1px) !important;
    }
    
    /* Top right language toggle specific styling */
    div[data-testid="column"]:last-child div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #2d1b69, #7c3aed) !important;
        color: #ffffff !important;
        border: 1px solid #7c3aed !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        padding: 6px 12px !important;
        font-weight: 600 !important;
        min-height: 32px !important;
        width: auto !important;
        float: right !important;
    }
    
    div[data-testid="column"]:last-child div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #5b21b6, #a855f7) !important;
        border-color: #a855f7 !important;
        transform: translateY(-1px) scale(1.02) !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
    }
    
    /* Form styling */
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        background: #21262d !important;
        color: #e6edf3 !important;
    }
    
    .stDateInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3fb950 !important;
        box-shadow: 0 0 0 3px rgba(63, 185, 80, 0.2) !important;
        outline: none !important;
    }
    
    /* Sidebar styling */
    .sidebar-content {
        background: #161b22;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #30363d;
    }
    
    /* Profile box styling */
    .profile-box {
        background: linear-gradient(135deg, rgba(255, 105, 180, 0.1), rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(255, 105, 180, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(255, 105, 180, 0.1);
    }
    
    .profile-box h3 {
        color: #ff69b4 !important;
        margin: 0 0 12px 0 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        text-align: center;
    }
    
    .profile-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 105, 180, 0.1);
    }
    
    .profile-item:last-child {
        border-bottom: none;
    }
    
    .profile-label {
        color: #e6edf3;
        font-weight: 500;
        font-size: 14px;
    }
    
    .profile-value {
        color: #ff69b4;
        font-weight: 600;
        font-size: 14px;
    }
    
    .sidebar-button {
        background: #21262d !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin: 4px 0 !important;
        width: 100% !important;
        text-align: left !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    .sidebar-button:hover {
        background: #30363d !important;
        border-color: #3fb950 !important;
        transform: translateY(-1px) !important;
    }
    
    /* Header styling */
    .app-header {
        text-align: center;
        padding: 0px 0 10px 0;
        background: transparent;
    }
    
    /* Profile setup container - centered vertically and horizontally */
    .profile-setup-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
    }
    
    .profile-form-box {
        background: linear-gradient(135deg, rgba(255, 105, 180, 0.05), rgba(255, 255, 255, 0.02));
        border: 1px solid rgba(255, 105, 180, 0.2);
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 16px rgba(255, 105, 180, 0.1);
        width: 100%;
        max-width: 500px;
        backdrop-filter: blur(10px);
    }
    
    .profile-form-title {
        color: #ff69b4 !important;
        text-align: center !important;
        margin-bottom: 24px !important;
        font-size: 24px !important;
        font-weight: 600 !important;
    }
    
    /* MaatriCare brand styling */
    .maatricare-brand {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #ff69b4, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        display: inline-block;
    }
    
    /* Chat interface header - less padding */
    .app-header.chat-header {
        padding: 20px 0 10px 0;
    }
    
    .app-title {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #ff69b4, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }
    
    .app-subtitle {
        font-size: 16px;
        color: #8b949e;
        margin-top: 8px;
    }
    
    /* Welcome message for empty chat */
    .welcome-message {
        text-align: center;
        padding: 60px 20px;
        color: #8b949e;
        background: #161b22;
        border-radius: 16px;
        border: 1px solid #30363d;
        margin: 20px 0;
    }
    
    .welcome-title {
        font-size: 24px;
        font-weight: 600;
        color: #e6edf3;
        margin-bottom: 12px;
    }
    
    .welcome-subtitle {
        font-size: 16px;
        line-height: 1.5;
        color: #8b949e;
    }
    
    /* Sidebar specific styling */
    .css-1d391kg {
        background-color: #0d1117 !important;
    }
    
    .css-1rs6os {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important;
    }
    
    /* Form labels */
    .stDateInput label,
    .stNumberInput label,
    .stTextArea label {
        color: #e6edf3 !important;
        font-weight: 500 !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #0f3a2d !important;
        border: 1px solid #3fb950 !important;
        color: #3fb950 !important;
    }
    
    .stError {
        background-color: #3d1a20 !important;
        border: 1px solid #f85149 !important;
        color: #f85149 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.set_page_config(page_title="🤰 মাতৃCare", layout="wide", initial_sidebar_state="auto")

# Language support dictionary
LANGUAGES = {
    "en": {
        "app_subtitle": "Your AI-powered maternal health assistant",
        "basic_info": "Basic Information",
        "lmp_label": "Last Menstrual Period (LMP) *",
        "lmp_help": "The first day of your last menstrual period",
        "age_label": "Age *",
        "age_help": "Your current age",
        "medical_history_label": "Medical History (Optional)",
        "medical_history_placeholder": "Any relevant medical conditions, previous pregnancies, allergies, etc.",
        "medical_history_help": "This information helps us provide better personalized recommendations",
        "create_profile_btn": "Create My Profile",
        "profile_created_success": "✅ Profile created successfully! Welcome to Maatri Care!",
        "fill_required_fields": "⚠️ Please fill in all required fields (LMP and Age) to continue.",
        "what_happening_week": "What's Happening This Week (Week {}):",
        "baby_size": "Your baby is now the size of a **{}**",
        "development": "**Development:** {}",
        "common_symptoms": "**Common symptoms:** {}",
        "feel_free_ask": "Feel free to ask me anything about your pregnancy journey!",
        "your_profile": "Your Profile",
        "current_week": "Current Week:",
        "age": "Age:",
        "years": "years",
        "lmp": "LMP:",
        "quick_actions": "Quick Actions",
        "view_full_profile": "📋 View Full Profile",
        "next_appointment": "🗓 Next Appointment",
        "nutrition_advice": "🥗 Nutrition Advice",
        "teleconsultation": "📞 Teleconsultation",
        "postpartum_care": "🏥 Postpartum Care",
        "welcome_title": 'Hello! I\'m your <span class="maatricare-brand">মাতৃCare</span> assistant',
        "welcome_subtitle": "I'm here to help you with your pregnancy journey. You can ask me about:<br>• Pregnancy symptoms and health concerns<br>• Appointment scheduling and reminders<br>• Nutrition and lifestyle advice<br>• General pregnancy information<br><br>How can I help you today?",
        "chat_input_placeholder": "Type your message here...",
        "assistant_label": "মাতৃCare Assistant",
        "user_label": "You",
        "language_toggle": "Language / ভাষা",
    },
    "bn": {
        "app_subtitle": "আপনার AI চালিত মাতৃস্বাস্থ্য সহায়ক",
        "basic_info": "মৌলিক তথ্য",
        "lmp_label": "শেষ মাসিক (LMP) *",
        "lmp_help": "আপনার শেষ মাসিকের প্রথম দিন",
        "age_label": "বয়স *",
        "age_help": "আপনার বর্তমান বয়স",
        "medical_history_label": "চিকিৎসার ইতিহাস (ঐচ্ছিক)",
        "medical_history_placeholder": "কোনো প্রাসঙ্গিক চিকিৎসা অবস্থা, পূর্ববর্তী গর্ভাবস্থা, এলার্জি ইত্যাদি।",
        "medical_history_help": "এই তথ্য আমাদের আরও ভাল ব্যক্তিগতকৃত সুপারিশ প্রদান করতে সহায়তা করে",
        "create_profile_btn": "আমার প্রোফাইল তৈরি করুন",
        "profile_created_success": "✅ প্রোফাইল সফলভাবে তৈরি হয়েছে! মাতৃCare-এ স্বাগতম!",
        "fill_required_fields": "⚠️ অনুগ্রহ করে সমস্ত প্রয়োজনীয় ক্ষেত্র (LMP এবং বয়স) পূরণ করুন।",
        "what_happening_week": "এই সপ্তাহে কি হচ্ছে (সপ্তাহ {}):",
        "baby_size": "আপনার শিশু এখন একটি **{}** এর আকারের",
        "development": "**বিকাশ:** {}",
        "common_symptoms": "**সাধারণ লক্ষণসমূহ:** {}",
        "feel_free_ask": "আপনার গর্ভাবস্থার যাত্রা সম্পর্কে আমাকে যেকোনো কিছু জিজ্ঞাসা করতে পারেন!",
        "your_profile": "আপনার প্রোফাইল",
        "current_week": "বর্তমান সপ্তাহ:",
        "age": "বয়স:",
        "years": "বছর",
        "lmp": "LMP:",
        "quick_actions": "দ্রুত কার্যক্রম",
        "view_full_profile": "📋 সম্পূর্ণ প্রোফাইল দেখুন",
        "next_appointment": "🗓 পরবর্তী অ্যাপয়েন্টমেন্ট",
        "nutrition_advice": "🥗 পুষ্টি পরামর্শ",
        "teleconsultation": "📞 টেলিকনসালটেশন",
        "postpartum_care": "🏥 প্রসবোত্তর যত্ন",
        "welcome_title": 'হ্যালো! আমি আপনার <span class="maatricare-brand">মাতৃCare</span> সহায়ক',
        "welcome_subtitle": "আমি আপনার গর্ভাবস্থার যাত্রায় সাহায্য করতে এখানে আছি। আপনি আমাকে জিজ্ঞাসা করতে পারেন:<br>• গর্ভাবস্থার লক্ষণ এবং স্বাস্থ্য উদ্বেগ<br>• অ্যাপয়েন্টমেন্ট সময়সূচী এবং অনুস্মারক<br>• পুষ্টি এবং জীবনযাত্রার পরামর্শ<br>• সাধারণ গর্ভাবস্থার তথ্য<br><br>আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
        "chat_input_placeholder": "এখানে আপনার বার্তা টাইপ করুন...",
        "assistant_label": "মাতৃCare সহায়ক",
        "user_label": "আপনি",
        "language_toggle": "Language / ভাষা",
    },
}

# Initialize session state
if "context" not in st.session_state:
    st.session_state.context = PatientContextManager()
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MaatriCareLangGraphOrchestrator()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_processed" not in st.session_state:
    st.session_state.last_processed = None
if "language" not in st.session_state:
    st.session_state.language = "en"  # Default language is English


# Function to get localized text
def get_text(key):
    return LANGUAGES[st.session_state.language].get(key, key)


def simple_markdown_to_html(text):
    """Convert basic markdown to HTML for better styling control"""
    import re

    # Convert **text** to <strong>text</strong>
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)

    # Convert lines starting with - to <li> items
    lines = text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        line = line.strip()
        if line.startswith("• "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:]}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line:
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("<br>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


ctx = st.session_state.context

# --- Profile Setup Screen (Only shown when no profile exists) ---
if ctx.state.get("profile") is None:
    # Language toggle in top right corner
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header3:
        current_lang_display = (
            "English" if st.session_state.language == "en" else "বাংলা"
        )
        if st.button(f"🌐 {current_lang_display}", key="lang_toggle_profile"):
            st.session_state.language = (
                "bn" if st.session_state.language == "en" else "en"
            )
            st.rerun()

    st.markdown(
        f"""
        <div class="app-header" style="margin-top: 20px;">
            <h1 class="app-title maatricare-brand">🤰 মাতৃCare</h1>
            <p class="app-subtitle">{get_text("app_subtitle")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:

            with st.form("profile_form", clear_on_submit=False):
                st.markdown(f"### {get_text('basic_info')}")
                lmp = st.date_input(
                    get_text("lmp_label"),
                    help=get_text("lmp_help"),
                )
                age = st.number_input(
                    get_text("age_label"),
                    min_value=18,
                    max_value=60,
                    step=1,
                    help=get_text("age_help"),
                )
                history = st.text_area(
                    get_text("medical_history_label"),
                    placeholder=get_text("medical_history_placeholder"),
                    help=get_text("medical_history_help"),
                )

                submitted = st.form_submit_button(
                    get_text("create_profile_btn"), use_container_width=True
                )

                if submitted and lmp and age:
                    try:
                        with st.spinner(show_loading_message("profile")):
                            # Create profile data for LangGraph system
                            profile_data = {
                                "age": int(age),
                                "lmp_date": lmp.isoformat(),
                                "medical_history": history or "Not specified",
                                "allergies": [],
                                "medications": [],
                            }

                            # Set profile in both context manager and orchestrator
                            ctx.set_profile(profile_data)
                            st.session_state.orchestrator.set_profile(profile_data)
                            st.session_state.context = ctx

                            # Validate profile was created successfully
                            if ctx.state.get("profile") is None:
                                raise ValueError(
                                    "Profile creation failed - please try again"
                                )

                            logger.info(
                                f"Profile created successfully for patient age {age}"
                            )

                        st.success(get_text("profile_created_success"))

                        # Add welcome interaction to chat history for better UX
                        current_week = "unknown"
                        week_number = 0
                        if ctx.state.get("medical_state"):
                            current_week = ctx.state["medical_state"].current_week
                            # Extract numeric week if it's a string like "Week 9"
                            if isinstance(
                                current_week, str
                            ) and current_week.lower().startswith("week"):
                                try:
                                    week_number = int(current_week.split()[-1])
                                except:
                                    week_number = 0
                            elif isinstance(current_week, (int, float)):
                                week_number = int(current_week)

                        # Get weekly development information
                        weekly_info = ""
                        if week_number > 0:
                            dev_info = get_weekly_development_info(week_number)
                            weekly_info = f"""**{get_text("what_happening_week").format(week_number)}**
                            • {get_text("baby_size").format(dev_info['size'])}
                            • {get_text("development").format(dev_info['development'])}
                            • {get_text("common_symptoms").format(dev_info['symptoms'])}"""

                        welcome_msg = f"""{weekly_info}

                        {get_text("feel_free_ask")}"""

                        st.session_state.chat_history = [("assistant", welcome_msg)]
                        st.rerun()

                    except Exception as e:
                        error_msg = handle_ui_error(e, "profile_creation")
                        st.error(f"❌ {error_msg}")
                        logger.error(f"Profile creation failed: {str(e)}")

                elif submitted:
                    st.error(get_text("fill_required_fields"))

    st.stop()

# --- Main Chat Interface (Only shown when profile exists) ---

# Language toggle in top right corner for chat interface
col_chat_header1, col_chat_header2, col_chat_header3 = st.columns([2, 1, 1])
with col_chat_header3:
    current_lang_display = "English" if st.session_state.language == "en" else "বাংলা"
    if st.button(f"🌐 {current_lang_display}", key="lang_toggle_chat"):
        st.session_state.language = "bn" if st.session_state.language == "en" else "en"
        st.rerun()

# Header for chat interface
st.markdown(
    """
    <div class="app-header chat-header" style="margin-top: 20px;">
        <h1 class="app-title maatricare-brand">🤰 মাতৃCare</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar with profile info and quick actions
with st.sidebar:
    # Profile summary
    if ctx.state.get("profile"):
        profile = ctx.state["profile"]
        medical = ctx.state.get("medical_state")
        current_week = medical.current_week if medical else "?"

        st.markdown(
            f"""
            <div class="profile-box">
                <h3>{get_text("your_profile")}</h3>
                <div class="profile-item">
                    <span class="profile-label">{get_text("current_week")}</span>
                    <span class="profile-value">{current_week}</span>
                </div>
                <div class="profile-item">
                    <span class="profile-label">{get_text("age")}</span>
                    <span class="profile-value">{profile.age} {get_text("years")}</span>
                </div>
                <div class="profile-item">
                    <span class="profile-label">{get_text("lmp")}</span>
                    <span class="profile-value">{profile.lmp_date}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f"### {get_text('quick_actions')}")

    if st.button(
        get_text("view_full_profile"), key="profile_btn", use_container_width=True
    ):
        st.session_state.chat_history.append(("user", "Show my complete profile"))

        # Use LangGraph orchestrator for profile display
        query = "show my profile"
        if st.session_state.language == "bn":
            query += " (Please respond in Bengali/বাংলা language)"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button(
        get_text("next_appointment"), key="appointment_btn", use_container_width=True
    ):
        st.session_state.chat_history.append(("user", "When is my next appointment?"))
        query = "show my next appointment schedule"
        if st.session_state.language == "bn":
            query += " (Please respond in Bengali/বাংলা language)"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button(
        get_text("nutrition_advice"), key="nutrition_btn", use_container_width=True
    ):
        st.session_state.chat_history.append(
            ("user", "Can you provide nutrition advice?")
        )
        query = "provide nutrition advice for my current pregnancy stage"
        if st.session_state.language == "bn":
            query += " (Please respond in Bengali/বাংলা language)"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button(
        get_text("teleconsultation"), key="telecon_btn", use_container_width=True
    ):
        st.session_state.chat_history.append(
            ("user", "Can you provide the teleconsultation plan?")
        )
        query = "help me schedule a teleconsultation"
        if st.session_state.language == "bn":
            query += " (Please respond in Bengali/বাংলা language)"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button(
        get_text("postpartum_care"), key="postpartum_btn", use_container_width=True
    ):
        st.session_state.chat_history.append(
            ("user", "Can you provide the postpartum care schedule?")
        )
        with st.spinner("Generating postpartum care schedule..."):
            query = "create my postpartum care schedule"
            if st.session_state.language == "bn":
                query += " (Please respond in Bengali/বাংলা language)"
            resp = st.session_state.orchestrator.process_query(query)
            resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

# Main chat container
col1, col2, col3 = st.columns([1, 8, 1])
with col2:
    # Chat history container
    chat_container = st.container()

    with chat_container:
        if not st.session_state.chat_history:
            # Welcome message when chat is empty
            st.markdown(
                f"""
                <div class="welcome-message">
                    <h3 class="welcome-title">{get_text("welcome_title")}</h3>
                    <p class="welcome-subtitle">
                        {get_text("welcome_subtitle")}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Display chat messages
            for role, msg in st.session_state.chat_history:
                if role == "user":
                    st.markdown(
                        f"""
                        <div class="message-container user-message-container">
                            <span class="user-label">{get_text("user_label")}</span>
                            <div class="user-message">{msg}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    # Display assistant label outside the bubble, then the styled message container
                    st.markdown(
                        f"""
                        <div class="message-container assistant-message-container">
                            <span class="assistant-label">{get_text("assistant_label")}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    # Convert markdown to HTML and display in a separate styled bubble
                    html_content = simple_markdown_to_html(msg)
                    st.markdown(
                        f"""
                        <div class="assistant-message-bubble">
                            <div class="assistant-message-content">
                                {html_content}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# Chat input at bottom
user_message = st.chat_input(get_text("chat_input_placeholder"))

if user_message and user_message != st.session_state.last_processed:
    # Add user message to history
    st.session_state.chat_history.append(("user", user_message))
    st.session_state.last_processed = user_message

    # Process the message
    with st.spinner(show_loading_message("response")):
        try:
            # Add language context to the query
            language_context = ""
            if st.session_state.language == "bn":
                language_context = " (Please respond in Bengali/বাংলা language)"

            query_with_language = user_message + language_context

            # Use LangGraph orchestrator to process the message
            # Ensure orchestrator has the latest profile data
            if ctx.state.get("profile"):
                profile_dict = {
                    "age": ctx.state["profile"].age,
                    "lmp_date": ctx.state["profile"].lmp_date,
                    "medical_history": ctx.state["profile"].medical_history,
                    "allergies": ctx.state["profile"].allergies or [],
                    "medications": ctx.state["profile"].medications or [],
                }
                st.session_state.orchestrator.set_profile(profile_dict)

            resp = st.session_state.orchestrator.process_query(query_with_language)

            # Clean the response to ensure no reasoning text appears
            resp = OutputProcessors.clean_all_llm_responses(resp)

            logger.info(f"Message processed successfully via LangGraph orchestrator")

        except Exception as e:
            error_msg = handle_ui_error(e, "chat_processing")
            resp = f"⚠️ {error_msg}\n\nPlease try asking your question differently, or contact support if the problem persists."
            logger.error(f"Chat processing error: {str(e)}")

    # Add assistant response to history
    st.session_state.chat_history.append(("assistant", resp))
    st.rerun()
