# 🤰 MaatriCare (মাতৃCare)

[![Python 3.10+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/langchain-0.1+-green.svg)](https://langchain.com)

**MaatriCare** is an AI-powered maternal health assistant designed specifically for pregnant women in Bangladesh and Bengali-speaking communities. The application provides personalized pregnancy care guidance, health monitoring, and comprehensive support throughout the maternal journey.

## 🌟 Key Features

### 🤖 AI-Powered Health Assistant
- **Multi-Agent Architecture**: Specialized AI agents for different aspects of maternal care
- **Conversational Interface**: Natural language interaction in English.
- **Personalized Recommendations**: Context-aware advice based on individual pregnancy profiles
- **Risk Assessment**: WHO guidelines-based symptom analysis and risk evaluation

### 🏥 Comprehensive Maternal Care
- **Pregnancy Tracking**: Week-by-week pregnancy development monitoring
- **ANC Scheduling**: Automated antenatal care appointment scheduling
- **Nutrition Planning**: Personalized meal plans featuring traditional Bangladeshi foods
- **Postpartum Care**: Complete post-delivery care guidance for both mother and newborn
- **Emergency Support**: 24/7 emergency response and critical symptom detection

### 📱 User-Friendly Interface
- **Modern Web UI**: Clean, responsive Streamlit-based interface
- **Profile Management**: Comprehensive patient profile creation and management
- **Chat Interface**: WhatsApp-style conversational experience
- **Quick Actions**: One-click access to common maternal care functions

## 🏗️ Architecture

### Multi-Agent System (LangGraph)
The application uses LangGraph to orchestrate multiple specialized AI agents:

1. **Intent Classifier**: Determines user request type (health, nutrition, scheduling, etc.)
2. **Risk Assessment Agent**: Evaluates symptoms and provides WHO-based risk analysis
3. **Conversational Health Agent**: Provides empathetic, personalized health guidance
4. **Nutrition Specialist**: Creates culturally appropriate meal plans
5. **ANC Scheduler**: Manages appointment scheduling and reminders
6. **Postpartum Coordinator**: Handles post-delivery care planning
7. **Emergency Response Agent**: Handles critical health situations

### Technical Stack
- **Backend**: Python 3.10+, LangChain, LangGraph
- **Frontend**: Streamlit with custom CSS styling
- **AI/ML**: Groq API for LLM capabilities
- **State Management**: LangGraph state machines with memory persistence
- **Logging**: Structured logging with comprehensive error handling

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- GROQ API key (for AI functionality)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/alMohimanul/MaatriCare.git
cd MaatriCare
```

2. **Create virtual environment:**
```bash
# Windows
python -m venv maatricare-venv
maatricare-venv\Scripts\activate

# Linux/Mac
python3 -m venv maatricare-venv
source maatricare-venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Environment configuration:**
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

5. **Run the application:**
```bash
python main.py
```

The application will start a Streamlit server, typically accessible at `http://localhost:8501`.

## 📋 Usage Guide

### 1. Profile Creation
- Enter your **Last Menstrual Period (LMP)** date
- Provide your **age**
- Add any relevant **medical history** (optional)
- The system automatically calculates current pregnancy week and trimester

### 2. Conversational Interface
- Ask questions in natural language, e.g.:
  - "What should I eat in my 24th week?"
  - "I'm experiencing nausea, is this normal?"
- Get personalized responses based on your pregnancy stage
- Use quick action buttons for common requests

### 3. Available Services
- **Health Queries**: "I'm experiencing nausea, is this normal?"
- **Nutrition Advice**: "What should I eat in my 24th week?"
- **Appointment Scheduling**: "When is my next ANC visit?"
- **Emergency Support**: "I'm having severe abdominal pain"
- **Postpartum Planning**: "What care do I need after delivery?"

## 🎯 Specialized Features

### Bangladeshi Context
- **Traditional Foods**: Recommendations include dal, shak, hilsa fish, and seasonal fruits
- **Cultural Practices**: Respects local customs and dietary habits
- **Healthcare System**: Aligned with Bangladesh's maternal healthcare protocols

### Emergency Response
- **Critical Symptom Detection**: Automatic identification of emergency situations
- **Immediate Action Plans**: Step-by-step emergency response guidance
- **Healthcare Provider Integration**: Quick access to emergency contacts

### Week-by-Week Tracking
- **Fetal Development**: Detailed information about baby's growth
- **Physical Changes**: What to expect each week
- **Symptom Guidance**: Normal vs. concerning symptoms by trimester

## 📊 Planned Features

Based on `new_features.txt`, upcoming enhancements include:

1. **Local Recipe Generator**: RAG system for Bangladeshi pregnancy recipes
2. **Conversational Memory**: Long-term conversation history and health tracking
3. **Progress Reports**: Automated weekly PDF health summaries
4. **OCR Integration**: Prescription reading and medication tracking

## 🛠️ Development

### Project Structure
```
MaatriCare/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── Agent/                  # AI agent orchestration
│   └── agent_orchestrator.py
├── Service/               # Core services
│   └── llm_service.py
├── UI/                    # Streamlit interface
│   └── ui.py
├── Utils/                 # Utilities and configurations
│   ├── constants.py
│   ├── logging_config.py
│   └── output_processors.py
└── logs/                  # Application logs
```

### Key Components
- **Agent Orchestrator**: Manages AI agent workflow using LangGraph
- **Patient Context Manager**: Handles user profiles and medical state
- **Output Processors**: Cleans and formats AI responses
- **Logging System**: Comprehensive logging for debugging and monitoring

## 🔒 Privacy & Security

- **Data Privacy**: No personal data is stored permanently on servers
- **Session-Based**: All data is session-based and cleared after use
- **Secure Communication**: Encrypted API communications
- **Medical Disclaimer**: All advice is supplementary to professional medical care

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## ⚠️ Medical Disclaimer

**MaatriCare is a supportive tool and NOT a replacement for professional medical care.** 

- Always consult qualified healthcare providers for medical decisions
- In emergencies, contact local emergency services immediately
- The application provides general guidance based on established medical guidelines
- Individual medical needs may vary and require professional assessment


## 🙏 Acknowledgments

- **WHO Maternal Health Guidelines** for medical reference standards
- **Bangladesh Ministry of Health** for local healthcare protocols
- **OpenAI** for AI capabilities
- **Streamlit Community** for the excellent web framework
- **LangChain Team** for the AI orchestration framework

---

**Made with ❤️ for mothers and families in Bangladesh**

*"Supporting every mother's journey with AI-powered care"*