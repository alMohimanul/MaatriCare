import sys
import os
import streamlit as st
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from Utils.logging_config import get_logger, setup_logging

    if not logging.getLogger().handlers:
        setup_logging()
    logger = get_logger("MaatriCare.UI")
    logger.info("🖥️  MaatriCare UI Starting Up")
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Using basic logging as fallback: {e}")

from Agent.langgraph_orchestrator import (
    PatientContextManager,
    MaatriCareLangGraphNativeOrchestrator as MaatriCareLangGraphOrchestrator,
)

from Utils.output_processors import OutputProcessors


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

    current_lang = getattr(st.session_state, "language", "en")
    error_messages = error_messages_bn if current_lang == "bn" else error_messages_en

    default_message = (
        "কিছু ভুল হয়ে গেছে। অনুগ্রহ করে আবার চেষ্টা করুন বা সমস্যা অব্যাহত থাকলে সহায়তার জন্য যোগাযোগ করুন।"
        if current_lang == "bn"
        else "Something went wrong. Please try again or contact support if the problem persists."
    )

    return error_messages.get(context, default_message)


def show_loading_message(operation: str, agent_type: str = None):
    """Show appropriate loading message based on operation with agent information"""
    loading_messages_en = {
        "orchestrator": "🤖 মাতৃCare Assistant is thinking...",
        "response": "💬 মাতৃCare Assistant is replying...",
        "emergency": "🚨 মাতৃCare Assistant is prioritizing your safety...",
        "profile": "🧬 Setting up your care profile...",
        "risk": "🧠 Checking your symptoms...",
        "schedule": "📅 Planning your ANC schedule...",
        "nutrition": "🥗 Preparing your personalized meal plan...",
        "teleconsult": "📞 Evaluating if a doctor’s consult is needed...",
        "health": "🔎 Finding reliable health information...",
        "exercise": "🤸‍♀️ Recommending safe pregnancy workouts...",
        "mood": "💝 Offering emotional support...",
        "general": "🩺 Reviewing your health details...",
    }

    loading_messages_bn = {
        "profile": "🔄 আপনার ব্যক্তিগতকৃত মাতৃযত্ন প্রোফাইল সেটআপ করা হচ্ছে...",
        "risk": "🔍 WHO মাতৃস্বাস্থ্য নির্দেশিকা ব্যবহার করে আপনার লক্ষণ বিশ্লেষণ করা হচ্ছে...",
        "schedule": "📅 আপনার সর্বোত্তম ANC অ্যাপয়েন্টমেন্ট সময়সূচী গণনা করা হচ্ছে...",
        "nutrition": "🥗 পুষ্টি এজেন্ট: ব্যক্তিগতকৃত সুপারিশ প্রস্তুত করা হচ্ছে...",
        "teleconsult": "📞 আপনার টেলিকনসালটেশন প্রয়োজন মূল্যায়ন করা হচ্ছে...",
        "health": "🔎 নির্ভরযোগ্য স্বাস্থ্য তথ্য অনুসন্ধান করা হচ্ছে...",
        "response": "💬 আপনার অনুরোধ প্রক্রিয়া করা হচ্ছে...",
        "exercise": "🤸‍♀️ ব্যায়াম এজেন্ট: আপনার জন্য নিরাপদ কার্যকলাপ খুঁজে বের করা হচ্ছে...",
        "mood": "💝 আবেগজনিত সহায়তা এজেন্ট: যত্নশীল নির্দেশনা প্রস্তুত করা হচ্ছে...",
        "emergency": "🚨 জরুরি এজেন্ট: আপনার নিরাপত্তাকে অগ্রাধিকার দেওয়া হচ্ছে...",
        "general": "🩺 স্বাস্থ্য এজেন্ট: ব্যাপক তথ্য সংগ্রহ করা হচ্ছে...",
        "orchestrator": "🤖 মাতৃCare: আপনার ব্যক্তিগতকৃত প্রতিক্রিয়া তৈরি করা হচ্ছে...",
    }

    current_lang = getattr(st.session_state, "language", "en")
    loading_messages = (
        loading_messages_bn if current_lang == "bn" else loading_messages_en
    )

    if agent_type and agent_type in loading_messages:
        return loading_messages[agent_type]

    return loading_messages.get(
        operation, loading_messages.get("response", "Processing...")
    )


def get_weekly_development_info(week: int) -> dict:
    """Get week-specific baby development information"""
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

    current_lang = getattr(st.session_state, "language", "en")
    weekly_info = weekly_info_bn if current_lang == "bn" else weekly_info_en

    if week in weekly_info:
        return weekly_info[week]

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
        color: red !important;
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
    
    /* Sidebar specific button overrides */
    div[data-testid="stSidebar"] .stButton > button {
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
        box-shadow: none !important;
    }
    
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: #30363d !important;
        border-color: #3fb950 !important;
        transform: translateY(-1px) !important;
        box-shadow: none !important;
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
    
    /* Enhanced markdown styling for structured responses */
    .alert-header {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        color: #ffffff;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 12px 0;
        font-weight: 600;
        border-left: 4px solid #b91c1c;
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
    }
    
    .alert-header .emoji {
        font-size: 18px;
        margin-right: 8px;
    }
    
    .section-header {
        color: #ff69b4 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        margin: 16px 0 8px 0 !important;
        padding: 8px 0 !important;
        border-bottom: 2px solid rgba(255, 105, 180, 0.3) !important;
    }
    
    .emergency-header {
        color: #dc2626 !important;
        background: rgba(220, 38, 38, 0.1) !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        border-left: 4px solid #dc2626 !important;
        margin: 12px 0 !important;
        font-weight: 700 !important;
    }
    
    .nutrition-header {
        color: #059669 !important;
        background: rgba(5, 150, 105, 0.1) !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        border-left: 4px solid #059669 !important;
        margin: 12px 0 !important;
        font-weight: 600 !important;
    }
    
    .exercise-header {
        color: #7c3aed !important;
        background: rgba(124, 58, 237, 0.1) !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        border-left: 4px solid #7c3aed !important;
        margin: 12px 0 !important;
        font-weight: 600 !important;
    }
    
    .tips-header {
        color: #ea580c !important;
        background: rgba(234, 88, 12, 0.1) !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        border-left: 4px solid #ea580c !important;
        margin: 12px 0 !important;
        font-weight: 600 !important;
    }
    
    .emergency-item {
        color: #dc2626 !important;
        background: rgba(220, 38, 38, 0.05) !important;
        padding: 6px 8px !important;
        margin: 4px 0 !important;
        border-radius: 4px !important;
        border-left: 3px solid #dc2626 !important;
        font-weight: 500 !important;
    }
    
    .nutrition-item {
        color: #059669 !important;
        background: rgba(5, 150, 105, 0.05) !important;
        padding: 6px 8px !important;
        margin: 4px 0 !important;
        border-radius: 4px !important;
        border-left: 3px solid #059669 !important;
    }
    
    .exercise-item {
        color: #7c3aed !important;
        background: rgba(124, 58, 237, 0.05) !important;
        padding: 6px 8px !important;
        margin: 4px 0 !important;
        border-radius: 4px !important;
        border-left: 3px solid #7c3aed !important;
    }
    
    .meal-item {
        background: rgba(255, 105, 180, 0.1) !important;
        color: #e6edf3 !important;
        padding: 8px 12px !important;
        margin: 6px 0 !important;
        border-radius: 6px !important;
        border-left: 3px solid #ff69b4 !important;
        font-weight: 500 !important;
    }
    
    .assistant-message-content h3 {
        margin: 16px 0 8px 0 !important;
        padding: 0 !important;
    }
    
    .assistant-message-content ul {
        margin: 8px 0 16px 0 !important;
        padding-left: 0 !important;
    }
    
    .assistant-message-content li {
        list-style: none !important;
        margin: 6px 0 !important;
        padding: 6px 8px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 4px !important;
        border-left: 2px solid #ff69b4 !important;
    }
    
    /* Enhanced emphasis styling */
    .assistant-message-content em {
        color: #ff69b4 !important;
        font-style: italic !important;
        font-weight: 500 !important;
    }
    
    /* Link styling for YouTube videos and other links */
    .assistant-message-content a {
        color: #58a6ff !important;
        text-decoration: underline !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        word-break: break-all !important;
    }
    
    .assistant-message-content a:hover {
        color: #79c0ff !important;
        text-decoration: underline !important;
    }
    
    /* YouTube link specific styling - only for special classes */
    .youtube-button {
        display: inline-block !important;
        background: linear-gradient(135deg, #ff0000, #ff6b6b) !important;
        color: #ffffff !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        margin: 4px 2px !important;
        font-size: 14px !important;
        box-shadow: 0 2px 4px rgba(255, 0, 0, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    
    .youtube-button:hover {
        background: linear-gradient(135deg, #cc0000, #ff5252) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(255, 0, 0, 0.3) !important;
        text-decoration: none !important;
    }
    
    .youtube-button::before {
        content: "▶️ ";
        margin-right: 4px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.set_page_config(page_title="🤰 মাতৃCare", layout="wide", initial_sidebar_state="auto")

if "context" not in st.session_state:
    st.session_state.context = PatientContextManager()
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MaatriCareLangGraphOrchestrator()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_processed" not in st.session_state:
    st.session_state.last_processed = None


def simple_markdown_to_html(text):
    """Convert basic markdown to HTML for better styling control with enhanced formatting"""
    import re

    # Convert **text** to <strong>text</strong>
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)

    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)

    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\)]+)\)",
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        text,
    )

    # Handle "Link: URL" format only if not already converted
    text = re.sub(
        r'(?<!href=")Link:\s*(https?://[^\s\n]+)',
        lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        text,
    )

    text = re.sub(
        r'(?<!href=")(?<!">)(https?://[^\s\n<>"]+)',
        lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        text,
    )

    text = re.sub(
        r"^(🚨.*?)\*\*(.*?)\*\*",
        r'<div class="alert-header"><span class="emoji">\1</span><strong>\2</strong></div>',
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"^([🥗🤸‍♀️💝📅🩺💬🔍📞🏥📋].*?)$",
        r'<div class="section-header">\1</div>',
        text,
        flags=re.MULTILINE,
    )

    # Convert lines starting with - to <li> items and handle nested structure
    lines = text.split("\n")
    html_lines = []
    in_list = False
    current_section = None

    for line in lines:
        line_stripped = line.strip()

        # Handle section headers (lines with **text** that aren't in lists)
        if (
            line_stripped.startswith("**")
            and line_stripped.endswith("**")
            and not in_list
        ):
            if in_list:
                html_lines.append("</ul>")
                in_list = False

            header_text = line_stripped[2:-2]  # Remove ** markers

            # Special styling for different types of headers
            if any(
                keyword in header_text.lower()
                for keyword in ["emergency", "urgent", "alert"]
            ):
                html_lines.append(f'<h3 class="emergency-header">{header_text}</h3>')
            elif any(
                keyword in header_text.lower()
                for keyword in ["nutrition", "meal", "food"]
            ):
                html_lines.append(f'<h3 class="nutrition-header">{header_text}</h3>')
            elif any(
                keyword in header_text.lower()
                for keyword in ["exercise", "activity", "safety"]
            ):
                html_lines.append(f'<h3 class="exercise-header">{header_text}</h3>')
            elif any(
                keyword in header_text.lower()
                for keyword in ["tips", "important", "guidelines"]
            ):
                html_lines.append(f'<h3 class="tips-header">{header_text}</h3>')
            else:
                html_lines.append(f'<h3 class="section-header">{header_text}</h3>')

            current_section = header_text.lower()
            continue

        # Handle list items
        if line_stripped.startswith("• ") or line_stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True

            list_content = line_stripped[2:]  # Remove bullet point

            # Style list items based on current section
            if current_section and "emergency" in current_section:
                html_lines.append(f'<li class="emergency-item">{list_content}</li>')
            elif current_section and "nutrition" in current_section:
                html_lines.append(f'<li class="nutrition-item">{list_content}</li>')
            elif current_section and "exercise" in current_section:
                html_lines.append(f'<li class="exercise-item">{list_content}</li>')
            else:
                html_lines.append(f"<li>{list_content}</li>")
        else:
            # Close list if we're leaving list items
            if in_list:
                html_lines.append("</ul>")
                in_list = False

            # Handle regular paragraphs
            if line_stripped:
                # Check for meal plan items (Breakfast:, Lunch:, etc.)
                if re.match(
                    r"^(Breakfast|Lunch|Dinner|Mid-Morning|Afternoon|Before Bed):",
                    line_stripped,
                ):
                    html_lines.append(f'<div class="meal-item">{line_stripped}</div>')
                else:
                    html_lines.append(f"<p>{line_stripped}</p>")
            else:
                html_lines.append("<br>")

    # Close any remaining list
    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


ctx = st.session_state.context

if ctx.state.get("profile") is None:
    st.markdown(
        f"""
        <div class="app-header" style="margin-top: 20px;">
            <h1 class="app-title maatricare-brand">🤰 মাতৃCare</h1>
            <p class="app-subtitle">Your trusted pregnancy companion for maternal and child health</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:

            with st.form("profile_form", clear_on_submit=False):
                st.markdown(f"### Basic Information")
                lmp = st.date_input(
                    "Last Menstrual Period (LMP)",
                    help="This helps calculate your pregnancy stage",
                )
                age = st.number_input(
                    "Age",
                    min_value=18,
                    max_value=60,
                    step=1,
                    help="Your current age for health planning",
                )
                history = st.text_area(
                    "Medical History (Optional)",
                    placeholder="Any relevant medical conditions, surgeries, or health concerns",
                    help="Share any important health information for personalized advice",
                )

                submitted = st.form_submit_button(
                    "Create Profile", use_container_width=True
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

                        st.success(
                            "Profile created successfully! Let's start your health journey together."
                        )

                        # Add welcome interaction to chat history for better UX
                        current_week = "unknown"
                        week_number = 0
                        if ctx.state.get("medical_state"):
                            medical_state = ctx.state["medical_state"]
                            current_week = (
                                medical_state.get("current_week", 0)
                                if medical_state
                                else 0
                            )
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
                            weekly_info = f"""**What's happening in Week {week_number}:**
                            • Baby size: {dev_info['size']}
                            • Development: {dev_info['development']}
                            • Common symptoms: {dev_info['symptoms']}"""

                        welcome_msg = f"""{weekly_info}

                        Feel free to ask me anything about your pregnancy, nutrition, exercise, or any concerns you have. I'm here to help! 💕"""

                        st.session_state.chat_history = [("assistant", welcome_msg)]
                        st.rerun()

                    except Exception as e:
                        error_msg = handle_ui_error(e, "profile_creation")
                        st.error(f"❌ {error_msg}")
                        logger.error(f"Profile creation failed: {str(e)}")

                elif submitted:
                    st.error(
                        "Please fill in all required fields (LMP and Age) to create your profile."
                    )

    st.stop()

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
        current_week = medical.get("current_week", "?") if medical else "?"

        st.markdown(
            f"""
            <div class="profile-box">
                <h3>Your Profile</h3>
                <div class="profile-item">
                    <span class="profile-label">Current Week:</span>
                    <span class="profile-value">{current_week}</span>
                </div>
                <div class="profile-item">
                    <span class="profile-label">Age:</span>
                    <span class="profile-value">{profile.get("age", "?")} years</span>
                </div>
                <div class="profile-item">
                    <span class="profile-label">LMP:</span>
                    <span class="profile-value">{profile.get("lmp_date", "?")}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f"### Quick Actions")

    if st.button("📋 View Full Profile", key="profile_btn", use_container_width=True):
        st.session_state.chat_history.append(("user", "Show my complete profile"))

        # Use LangGraph orchestrator for profile display
        query = "show my profile"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button("🗓 Next Appointment", key="appointment_btn", use_container_width=True):
        st.session_state.chat_history.append(("user", "When is my next appointment?"))
        query = "show my next appointment schedule"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button("🥗 Nutrition Advice", key="nutrition_btn", use_container_width=True):
        st.session_state.chat_history.append(
            ("user", "Can you provide nutrition advice?")
        )
        query = "provide nutrition advice for my current pregnancy stage"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button("📞 Teleconsultation", key="telecon_btn", use_container_width=True):
        st.session_state.chat_history.append(
            ("user", "Can you provide the teleconsultation plan?")
        )
        query = "help me schedule a teleconsultation"
        resp = st.session_state.orchestrator.process_query(query)
        resp = OutputProcessors.clean_all_llm_responses(resp)
        st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    if st.button("🏥 Postpartum Care", key="postpartum_btn", use_container_width=True):
        st.session_state.chat_history.append(
            ("user", "Can you provide the postpartum care schedule?")
        )
        with st.spinner("Generating postpartum care schedule..."):
            query = "create my postpartum care schedule"
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
                    <h3 class="welcome-title">Hello! I'm your <span class="maatricare-brand">মাতৃCare</span> agent</h3>
                    <p class="welcome-subtitle">
                        I'm here to help you with your pregnancy journey. You can ask me about:<br>• Pregnancy symptoms and health concerns<br>• Appointment scheduling and reminders<br>• Nutrition and lifestyle advice<br>• General pregnancy information<br><br>How can I help you today?
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
                            <span class="user-label">You</span>
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
                            <span class="assistant-label">মাতৃCare Agent</span>
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
user_message = st.chat_input("Type your message here...")

if user_message and user_message != st.session_state.last_processed:
    # Add user message to history
    st.session_state.chat_history.append(("user", user_message))
    st.session_state.last_processed = user_message

    # Determine likely agent type for better spinner messages
    def detect_agent_type(message):
        message_lower = message.lower()

        # Emergency detection
        emergency_keywords = [
            "pain",
            "bleeding",
            "emergency",
            "urgent",
            "help",
            "hospital",
            "doctor now",
        ]
        if any(keyword in message_lower for keyword in emergency_keywords):
            return "emergency"

        # Nutrition detection
        nutrition_keywords = [
            "food",
            "eat",
            "diet",
            "nutrition",
            "meal",
            "hungry",
            "vitamin",
            "recipe",
            "breakfast",
            "lunch",
            "dinner",
        ]
        if any(keyword in message_lower for keyword in nutrition_keywords):
            return "nutrition"

        # Exercise detection
        exercise_keywords = [
            "exercise",
            "workout",
            "yoga",
            "walk",
            "fitness",
            "active",
            "movement",
            "stretch",
        ]
        if any(keyword in message_lower for keyword in exercise_keywords):
            return "exercise"

        # Mood/emotional detection
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
        if any(keyword in message_lower for keyword in mood_keywords):
            return "mood"

        # Scheduling detection
        scheduling_keywords = [
            "appointment",
            "schedule",
            "visit",
            "checkup",
            "doctor",
            "anc",
            "when should",
        ]
        if any(keyword in message_lower for keyword in scheduling_keywords):
            return "schedule"

        return "general"

    detected_agent = detect_agent_type(user_message)

    # Process the message with intelligent spinner
    with st.spinner(show_loading_message("response", detected_agent)):
        try:
            # Use LangGraph orchestrator to process the message
            # Ensure orchestrator has the latest profile data
            if ctx.state.get("profile"):
                profile_dict = {
                    "age": ctx.state["profile"].get("age"),
                    "lmp_date": ctx.state["profile"].get("lmp_date"),
                    "medical_history": ctx.state["profile"].get("medical_history"),
                    "allergies": ctx.state["profile"].get("allergies", []),
                    "medications": ctx.state["profile"].get("medications", []),
                }
                st.session_state.orchestrator.set_profile(profile_dict)

            resp = st.session_state.orchestrator.process_query(user_message)

            # Clean the response to ensure no reasoning text appears
            resp = OutputProcessors.clean_all_llm_responses(resp)

            logger.info(
                f"Message processed successfully via LangGraph orchestrator - Agent: {detected_agent}"
            )

        except Exception as e:
            error_msg = handle_ui_error(e, "chat_processing")
            resp = f"⚠️ {error_msg}\n\nPlease try asking your question differently, or contact support if the problem persists."
            logger.error(f"Chat processing error: {str(e)}")

    # Add assistant response to history
    st.session_state.chat_history.append(("assistant", resp))
    st.rerun()
