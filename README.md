# 🚀 ATS Resume Optimizer API v2.0

**FastAPI-based AI-powered resume optimization for maximum ATS compatibility**

---

## 📋 Features

### Core ATS Analysis
- ✅ **ATS Compatibility Score (0-100)**: Comprehensive scoring algorithm
- ✅ **Keyword Match Analysis**: Semantic matching against job descriptions
- ✅ **Missing Skills Detection**: Categorized skill gap analysis
- ✅ **Resume Parsing**: Support for PDF and DOCX files
- ✅ **Job Description Upload**: Extract and analyze requirements
- ✅ **Section Validation**: Education, Experience, Skills, Projects verification
- ✅ **Resume Strengths & Weaknesses**: Detailed improvement suggestions

### Resume Optimization
- ✅ **One-Click Improvement**: Auto-optimize while preserving format
- ✅ **Multiple Export Formats**: PDF, DOCX, Plain Text, Markdown
- ✅ **Customizable Themes**: Professional, Modern, Minimalist designs
- ✅ **Batch Processing**: Export in multiple formats simultaneously
- ✅ **Download Optimized Resume**: In original or ATS-optimized format

---

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104+
- **Server**: Uvicorn
- **AI Engine**: Google Gemini 1.5 Flash
- **NLP**: SentenceTransformers (semantic matching)
- **Document Processing**:
  - PyMuPDF (PDF extraction)
  - python-docx (DOCX handling)
  - ReportLab (PDF generation)
- **Database**: None (stateless API)
- **Containerization**: Docker & Docker Compose

---

## 📦 Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Google Gemini API Key (free tier available)
- 2GB RAM minimum
- 500MB disk space

---

## ⚡ Quick Start

### Option 1: Local Development

```bash
# Clone repository
git clone https://github.com/sairamkarpurapu2803/Ats_resume.git
cd Ats_resume

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run server
uvicorn main:app --reload
```

Access at: `http://localhost:8000`

### Option 2: Docker Deployment

```bash
# Build image
docker build -t ats-resume-api .

# Run container
docker run -d \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your_key_here" \
  --name ats-resume-api \
  ats-resume-api
```

### Option 3: Docker Compose

```bash
# Set environment variable
export GEMINI_API_KEY="your_gemini_api_key"

# Start services
docker-compose up -d

# View logs
docker-compose logs -f ats-resume-api
```

---

## 📚 API Documentation

Access interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### 1. Authentication
```bash
POST /api/v1/auth/validate-api-key
{
  "gemini_api_key": "your_key_here"
}
```

#### 2. Resume Upload & Parsing
```bash
POST /api/v1/resume/upload
# Form data: file (PDF/DOCX)

POST /api/v1/resume/validate
{
  "resume_data": {...}
}
```

#### 3. ATS Analysis
```bash
POST /api/v1/analysis/analyze
{
  "resume_data": {...},
  "job_description": "string",
  "detailed": true
}

Response:
{
  "ats_score": 85,
  "match_percentage": 78,
  "matching_keywords": [...],
  "missing_keywords": [...],
  "section_scores": {...},
  "strengths": [...],
  "weaknesses": [...],
  "suggestions": [...]
}
```

#### 4. Skill Gap Analysis
```bash
POST /api/v1/analysis/skill-gap
{
  "resume_data": {...},
  "job_description": "string"
}
```

#### 5. Resume Optimization
```bash
POST /api/v1/export/optimize
{
  "resume_data": {...},
  "job_description": "string",
  "preserve_format": true
}
```

#### 6. Export Resume
```bash
POST /api/v1/export/export
{
  "resume_data": {...},
  "job_description": "string",
  "format": "pdf|docx|plaintext|markdown",
  "theme": "professional|modern|minimalist"
}
```

---

## 📂 Project Structure

```
Ats_resume/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── .env.example           # Environment variables template
├── README.md              # This file
│
├── api/
│   └── routes/
│       ├── __init__.py
│       ├── auth.py        # Authentication endpoints
│       ├── health.py      # Health check endpoints
│       ├── resume.py      # Resume upload/validation
│       ├── analysis.py    # ATS analysis endpoints
│       └── export.py      # Export endpoints
│
├── services/
│   ├── __init__.py
│   ├── resume_parser.py   # Resume parsing logic
│   ├── ats_analyzer.py    # ATS analysis engine
│   └── resume_optimizer.py # Resume optimization & export
│
├── utils/
│   ├── __init__.py
│   ├── errors.py          # Custom exceptions
│   ├── logger.py          # Logging configuration
│   └── workspace.py       # Workspace initialization
│
├── uploads/               # Uploaded resume storage
├── exports/               # Exported resume storage
├── logs/                  # Application logs
└── templates/             # Resume templates
```

---

## 🔑 Getting Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API key"
3. Copy the key
4. Add to `.env` file: `GEMINI_API_KEY=your_key_here`

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Upload resume
curl -X POST "http://localhost:8000/api/v1/resume/upload" \
  -F "file=@resume.pdf"

# Analyze resume
curl -X POST "http://localhost:8000/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d @analysis_request.json
```

---

## 📊 Performance Notes

- First request: ~3-5s (model loading)
- Subsequent requests: ~1-2s
- File upload limit: 10MB
- Concurrent requests: Depends on server resources

---

## 🐛 Troubleshooting

### Issue: "Gemini API Key not configured"
```bash
# Solution: Add key to .env or pass via environment
export GEMINI_API_KEY="your_key_here"
uvicorn main:app --reload
```

### Issue: "ModuleNotFoundError"
```bash
# Solution: Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Issue: "Port 8000 already in use"
```bash
# Solution: Use different port
uvicorn main:app --port 8001
```

---

## 🚀 Production Deployment

### Using Gunicorn + Nginx

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📝 License

MIT License - feel free to use this project

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

---

## ⭐ Support

If you find this project useful, please **star ⭐** the repository!

---

## 📞 Contact

For issues and questions:
- GitHub Issues: [Project Issues](https://github.com/sairamkarpurapu2803/Ats_resume/issues)
- Email: sairamkarpurapu2803@gmail.com

---

**Made with ❤️ for job seekers everywhere**
