# SkyScraper.bot Backend API

Enterprise-grade web scraping platform with conversational AI, legal compliance, and R dashboard export capabilities.

## 🚀 Features

- **Conversational AI Interface**: Extract data using natural language commands
- **Legal Compliance Engine**: Automatic robots.txt checking and ToS analysis
- **Full API Access**: Complete REST API with webhooks and SDKs
- **R Dashboard Export**: Generate R Shiny dashboards automatically
- **Real-time Streaming**: WebSocket streaming with guaranteed delivery
- **Enterprise Collaboration**: Team workspaces and role-based access
- **Advanced Anti-Detection**: Military-grade proxy rotation and fingerprinting protection

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy
- **Cache/Queue**: Redis
- **AI Integration**: OpenAI, Anthropic, LangChain
- **Web Scraping**: Playwright, BeautifulSoup, Selenium
- **Deployment**: Render, Docker
- **Monitoring**: Sentry, Structured Logging

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 13+ (for production)
- Redis 6+ (for caching and job queue)
- Node.js 18+ (for Playwright)

## 🔧 Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/skyscraper-bot.git
cd skyscraper-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Start Local Services

```bash
# Start Redis (using Docker)
docker run -d -p 6379:6379 redis:7

# Start PostgreSQL (using Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=skyscraper_dev postgres:15
```

### 6. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 🚀 Deployment on Render

### 1. Fork this Repository

Fork this repository to your GitHub account.

### 2. Connect to Render

1. Sign up for [Render](https://render.com)
2. Connect your GitHub account
3. Create a new Web Service
4. Select your forked repository

### 3. Configure Render Settings

**Build Command:**
```bash
chmod +x build.sh && ./build.sh
```

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
```

### 4. Environment Variables

Set these in the Render dashboard:

```
ENVIRONMENT=production
DATABASE_URL=<your-postgres-connection-string>
REDIS_URL=<your-redis-connection-string>
OPENAI_API_KEY=<your-openai-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
SECRET_KEY=<your-secret-key>
```

### 5. Auto-Deploy with render.yaml

Place the `render.yaml` file in your repository root for infrastructure-as-code deployment:

```bash
# This will automatically create:
# - Web service for the API
# - PostgreSQL database
# - Redis instance
# - Background worker (optional)
```

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build the image
docker build -t skyscraper-bot .

# Run with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  -e OPENAI_API_KEY=your-key \
  skyscraper-bot
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/skyscraper
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: skyscraper
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    
volumes:
  postgres_data:
```

## 📊 API Documentation

Once running, visit:
- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🔑 API Endpoints

### Core Endpoints

```
POST /v1/extract              # Main data extraction endpoint
GET  /v1/jobs/{job_id}        # Get extraction job status
GET  /v1/jobs                 # List recent jobs
GET  /v1/compliance/check     # Check legal compliance
GET  /v1/health               # Health check
```

### Authentication

```
POST /v1/auth/signup          # User registration
POST /v1/auth/signin          # User authentication
```

### Example Usage

```python
import httpx

# Start extraction
response = httpx.post("https://api.skyscraper.bot/v1/extract", json={
    "url": "https://example.com",
    "instruction": "Extract all product names and prices",
    "format": "r_dashboard",
    "structured_extraction": True,
    "webhook_url": "https://yourapp.com/webhook"
})

job = response.json()
print(f"Job ID: {job['job_id']}")

# Check status
status = httpx.get(f"https://api.skyscraper.bot/v1/jobs/{job['job_id']}")
print(status.json())
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## 📈 Monitoring

### Health Checks
- **Endpoint**: `/v1/health`
- **Uptime**: Configured for Render auto-restart
- **Metrics**: Active jobs, registered users, system status

### Logging
- **Structured logging** with JSON format
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Sentry integration** for error tracking

### Performance
- **Rate limiting** per user tier
- **Request timeout** configuration
- **Connection pooling** for database
- **Redis caching** for frequent requests

## 🔒 Security

- **CORS** configuration for frontend domains
- **JWT** authentication with secure tokens
- **Rate limiting** to prevent abuse
- **Input validation** with Pydantic models
- **SQL injection** protection via SQLAlchemy
- **Environment variable** management for secrets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.skyscraper.bot](https://docs.skyscraper.bot)
- **Issues**: [GitHub Issues](https://github.com/yourusername/skyscraper-bot/issues)
- **Email**: support@skyscraper.bot
- **Discord**: [Join our community](https://discord.gg/skyscraper)

## 🗺️ Roadmap

- [ ] Chrome Extension for point-and-click scraping
- [ ] Advanced AI model fine-tuning
- [ ] Multi-language support
- [ ] Industry-specific templates
- [ ] Enterprise SSO integration
- [ ] Advanced analytics dashboard
- [ ] White-label solutions

---

**Made with ❤️ by the SkyScraper.bot team**

Deploy your first scraper in minutes: [Get Started](https://skyscraper.bot)
