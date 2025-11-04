<div align="center">

# ✨ StoryWeave AI

**AI-Powered Story Creation Platform | Transform Ideas into Compelling Narratives**

[![CI](https://img.shields.io/github/actions/workflow/status/DiveshK007/StoryWeave_AI/.github/workflows/ci.yml?branch=main&label=CI&logo=github)](https://github.com/DiveshK007/StoryWeave_AI/actions)
[![Security Scan](https://img.shields.io/github/actions/workflow/status/DiveshK007/StoryWeave_AI/.github/workflows/security-scan.yml?branch=main&label=Security&logo=github)](https://github.com/DiveshK007/StoryWeave_AI/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/react-18.0+-61dafb.svg)](https://reactjs.org/)

**🚀 [Live Demo](#-demo) | 📖 [Documentation](#-documentation) | 🎯 [Features](#-key-features) | 🛠️ [Installation](#-installation)**

</div>

---

## 📖 About

StoryWeave AI is an intelligent storytelling platform that empowers writers to craft compelling narratives using the power of AI. Transform your ideas into fully-realized stories with AI-generated outlines, scene expansion, character development, and real-time collaborative editing.

### The Problem

Writers often struggle with:
- **Writer's Block**: Difficulty developing story ideas into structured narratives
- **Consistency Issues**: Maintaining character consistency across scenes
- **Collaboration Challenges**: Difficulty coordinating with co-writers in real-time
- **Time Constraints**: Spending excessive time on manual story structuring

### Our Solution

StoryWeave AI combines **Retrieval-Augmented Generation (RAG)**, advanced LLMs, and real-time collaboration to provide:
- 🤖 **AI-Powered Story Generation**: Transform premises into structured outlines
- 👥 **Character Development**: Create rich, consistent characters with relationship tracking
- 🔄 **Real-Time Collaboration**: Work together seamlessly with live editing
- 📊 **Analytics & Insights**: Track your writing progress and story metrics
- 🎨 **Modern UI**: Beautiful, intuitive interface inspired by Linear and Vercel

---

## ✨ Key Features

### 🎯 Core Features

- **📝 Story Generation**
  - Generate story outlines from simple premises
  - AI-powered scene expansion with context awareness
  - Support for multiple genres (Fantasy, Sci-Fi, Mystery, Thriller, etc.)
  - Customizable story length (Short Story, Novella, Novel)

- **👥 Character Development**
  - AI-generated character profiles (physical description, personality, backstory)
  - Character consistency tracking across scenes
  - Visual relationship mapping between characters
  - Character mention tracking and analysis

- **🔄 Real-Time Collaboration**
  - WebSocket-based live editing
  - Presence indicators (see who's viewing/editing)
  - Beat locking system (prevents conflicts)
  - Real-time chat for collaborators
  - Comment threads on beats and scenes

- **📊 Analytics & Monitoring**
  - Product analytics with Mixpanel
  - Error tracking with Sentry
  - Story creation metrics
  - User engagement tracking
  - Admin dashboard for insights

- **🎨 Modern Frontend**
  - Production-ready React + TypeScript UI
  - Tailwind CSS design system
  - Dark mode optimized
  - Responsive design (mobile, tablet, desktop)
  - Drag-and-drop beat editor
  - Inline editing capabilities

### 🔧 Technical Features

- **RAG (Retrieval-Augmented Generation)**: Ingest knowledge base files for context-aware generation
- **Vector Search**: Semantic search across story knowledge base
- **RESTful API**: Comprehensive FastAPI backend
- **WebSocket Support**: Real-time bidirectional communication
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **CI/CD**: Automated testing and deployment pipelines
- **Type Safety**: Full TypeScript + Python type hints

---

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Zustand** - State management
- **Axios** - HTTP client
- **@dnd-kit** - Drag & drop
- **Lucide React** - Icons

### Backend
- **FastAPI** - Web framework
- **Python 3.10+** - Programming language
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **FAISS** - Vector similarity search
- **WebSockets** - Real-time communication
- **Redis** (optional) - Pub/sub for scaling

### AI & ML
- **NVIDIA NIM** - LLM inference
- **Embedding Models** - Vector embeddings
- **RAG Pipeline** - Context retrieval

### DevOps & Monitoring
- **GitHub Actions** - CI/CD
- **Sentry** - Error tracking
- **Mixpanel** - Product analytics
- **Docker** - Containerization
- **pytest** - Testing framework

---

## 📸 Screenshots

> **Note**: Screenshots will be added. Place screenshots in `docs/screenshots/` directory.

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Story Editor
![Story Editor](docs/screenshots/story-editor.png)

### Character Development
![Characters](docs/screenshots/characters.png)

### Real-Time Collaboration
![Collaboration](docs/screenshots/collaboration.png)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Git**
- (Optional) **Docker** and **Docker Compose**

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/DiveshK007/StoryWeave_AI.git
cd StoryWeave_AI
```

#### 2. Backend Setup

```bash
cd agentic-aws-nvidia-demo/services/orchestrator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration (see Configuration section)
# Then run:
uvicorn app.main:app --reload --port 8080
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your API URL
# Then run:
npm run dev
```

#### 4. Access the Application

- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Frontend**: http://localhost:5173

---

## 🐳 Docker Deployment

### Quick Start with Docker Compose

```bash
docker-compose up -d
```

This will start:
- Backend API on port 8080
- Frontend on port 5173
- PostgreSQL database (if configured)

### Docker Compose Configuration

See `docker-compose.yml` for full configuration options.

---

## ⚙️ Configuration

### Backend Environment Variables

Create `.env` in `agentic-aws-nvidia-demo/services/orchestrator/`:

```bash
# Database
DATABASE_URL=sqlite:///./stories.db  # Or PostgreSQL URL

# AI/LLM (Optional - uses mock mode if not set)
NIM_API_KEY=your_nim_api_key
NIM_API_URL=https://integrate.api.nvidia.com/v1

# Sentry (Optional)
SENTRY_DSN=your_sentry_dsn
SENTRY_RELEASE=1.0.0
ENVIRONMENT=development

# Mixpanel (Optional)
MIXPANEL_TOKEN=your_mixpanel_token
MIXPANEL_API_SECRET=your_api_secret
APP_VERSION=1.0.0

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads

# Vector Store
INDEX_DIR=./indices
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Frontend Environment Variables

Create `.env` in `frontend/`:

```bash
# API Configuration
VITE_API_URL=http://localhost:8080

# Sentry (Optional)
VITE_SENTRY_DSN=your_sentry_dsn
VITE_SENTRY_RELEASE=1.0.0

# Mixpanel (Optional)
VITE_MIXPANEL_TOKEN=your_mixpanel_token
VITE_APP_VERSION=1.0.0
```

See `.env.example` files for detailed options.

---

## 📚 API Documentation

### Core Endpoints

#### Stories
- `GET /stories` - List all stories
- `POST /stories` - Create new story
- `GET /stories/{id}` - Get story details
- `PUT /stories/{id}` - Update story
- `DELETE /stories/{id}` - Delete story

#### Story Generation
- `POST /ingest` - Upload knowledge base files (multipart/form-data)
- `POST /generate_outline` - Generate story outline from premise
- `POST /expand_scene` - Expand a scene from outline
- `GET /stories/{id}/export?format=pdf|docx|txt` - Export story

#### Beats
- `GET /stories/{id}/beats` - Get all beats for a story
- `POST /stories/{id}/beats` - Create new beat
- `PUT /beats/{id}` - Update beat
- `DELETE /beats/{id}` - Delete beat
- `POST /stories/{id}/beats/reorder` - Reorder beats

#### Characters
- `POST /characters/generate` - Generate character with AI
- `GET /stories/{id}/characters` - Get all characters
- `GET /characters/{id}` - Get character details
- `PUT /characters/{id}` - Update character
- `DELETE /characters/{id}` - Delete character
- `POST /characters/{id}/analyze-consistency` - Check consistency

#### Collaboration
- `WebSocket /ws/story/{id}` - Real-time collaboration
- `POST /stories/{id}/share` - Share story with collaborators
- `GET /stories/{id}/permissions` - Get story permissions
- `POST /comments` - Add comment
- `GET /stories/{id}/comments` - Get all comments

#### Analytics (Admin)
- `GET /admin/analytics/overview` - Overview metrics
- `GET /admin/analytics/genres` - Genre popularity
- `GET /admin/analytics/funnel` - Feature usage funnel
- `GET /admin/analytics/users` - User analytics

### Interactive API Docs

Visit http://localhost:8080/docs for interactive Swagger documentation.

---

## 🧪 Testing

### Backend Tests

```bash
cd agentic-aws-nvidia-demo/services/orchestrator

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────┐
│   Client    │
│  (React)    │
└──────┬──────┘
       │
       │ HTTP/WebSocket
       │
┌──────▼──────────────────┐
│   FastAPI Backend       │
│  ┌──────────────────┐   │
│  │  REST API        │   │
│  │  WebSocket       │   │
│  │  Auth Middleware │   │
│  └────────┬─────────┘   │
│           │              │
│  ┌────────▼─────────┐   │
│  │  Business Logic  │   │
│  │  - Story Gen     │   │
│  │  - Characters    │   │
│  │  - Collaboration │   │
│  └────────┬─────────┘   │
└───────────┼──────────────┘
            │
    ┌───────┴────────┐
    │                │
┌───▼────┐    ┌─────▼─────┐
│Database│    │ Vector DB │
│SQLite/ │    │  (FAISS)  │
│Postgres│    └───────────┘
└────────┘
```

### Component Structure

```
StoryWeave_AI/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities & API clients
│   │   ├── stores/          # State management
│   │   └── types/           # TypeScript types
│   └── package.json
│
├── agentic-aws-nvidia-demo/
│   └── services/orchestrator/  # FastAPI backend
│       ├── app/
│       │   ├── main.py         # FastAPI app
│       │   ├── models.py       # Database models
│       │   ├── crud.py         # CRUD operations
│       │   ├── retrieval.py    # RAG pipeline
│       │   ├── character_*.py  # Character features
│       │   └── collaboration_*.py  # Collaboration
│       ├── tests/              # Test suite
│       └── requirements.txt
│
└── docs/                      # Documentation
```

---

## 🔒 Security

- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (React auto-escaping)
- CORS configuration
- File upload validation
- Rate limiting (ready for implementation)
- Authentication ready (JWT compatible)

---

## 🤝 Contributing

This is a hackathon project. For questions or feedback, please open an issue on GitHub.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 Roadmap

### Current Version (v1.0.0)
- ✅ Story generation with RAG
- ✅ Character development
- ✅ Real-time collaboration
- ✅ Analytics & monitoring
- ✅ Modern UI/UX

### Upcoming Features
- [ ] User authentication & authorization
- [ ] Advanced story templates
- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] AI-powered editing suggestions
- [ ] Story versioning & history
- [ ] Export to more formats (EPUB, Kindle)
- [ ] Integration with writing tools (Scrivener, etc.)

See [ROADMAP.md](docs/ROADMAP.md) for detailed roadmap.

---

## 👥 Team

**StoryWeave AI Development Team**

- **Lead Developer**: [Your Name]
- **AI/ML Engineer**: [Team Member]
- **Frontend Developer**: [Team Member]
- **Backend Developer**: [Team Member]

---

## 🙏 Acknowledgments

- **NVIDIA NIM** for LLM inference
- **FastAPI** team for the amazing framework
- **React** team for the UI library
- **Tailwind CSS** for the design system
- All open-source contributors

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DiveshK007/StoryWeave_AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DiveshK007/StoryWeave_AI/discussions)
- **Email**: support@storyweave.ai (if available)

---

## 🌟 Show Your Support

If you find this project helpful, please give it a ⭐ on GitHub!

---

<div align="center">

**Built with ❤️ by the StoryWeave AI Team**

[⬆ Back to Top](#-storyweave-ai)

</div>
