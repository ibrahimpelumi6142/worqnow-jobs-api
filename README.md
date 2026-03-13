# WorqNow Jobs API

> Free, open-source job search API - Save $300/year vs paid alternatives

**Works Globally** | **Bot-Friendly** | **5-Minute Setup**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Why This Exists

Stop paying **$25+/month** for job search APIs!

This free, self-hosted API was built for [WorqNow](https://worqnow.ai) - a WhatsApp job bot serving 200+ users across Africa. Now available for everyone building job bots, career platforms, or job boards.

**Powered by [JobSpy](https://github.com/culclasure/jobspy)** - we just wrapped it in a production-ready FastAPI service.

---

## 🌟 Features

- 🌍 **Global Coverage** - Nigeria, USA, UK, India, UAE + 190 countries
- 🔍 **Multi-Source** - Indeed, LinkedIn, ZipRecruiter, Glassdoor, Bayt, Naukri
- 📱 **Bot-Optimized** - Perfect for WhatsApp, Telegram, Discord bots
- 🚀 **Natural Language** - `"developer in Lagos"` just works
- 💰 **$0 Cost** - Free forever, no usage limits
- ⚡ **Fast** - Typical response in 2-3 seconds
- 🔓 **Open Source** - MIT licensed, modify freely

---

## 💰 Cost Comparison

| Service | Monthly Cost | Annual Cost |
|---------|--------------|-------------|
| **jsearch** | $25+ | $300+ |
| **SerpAPI Jobs** | $50+ | $600+ |
| **This API (self-hosted)** | **$0** | **$0** |

*Plus VPS costs (~$5/mo) if you don't already have a server*

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/ibrahimpelumi6142/worqnow-jobs-api.git
cd worqnow-jobs-api

# Install
pip install -r requirements.txt

# Run
python main.py
```

**That's it!** API running at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

---

## 📖 Usage

### Basic Search

```bash
# Lagos, Nigeria
curl "http://localhost:8000/api/v1/search?query=developer%20in%20Lagos"

# Remote jobs
curl "http://localhost:8000/api/v1/search?query=remote%20python%20developer"

# New York, USA
curl "http://localhost:8000/api/v1/search?query=software%20engineer%20in%20New%20York"
```

### Python Example

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/search",
    params={"query": "developer in Lagos"}
)

jobs = response.json()['data']

for job in jobs:
    print(f"{job['job_title']} at {job['employer_name']}")
    print(f"Location: {job['job_city']}, {job['job_country']}")
    print(f"Apply: {job['job_apply_link']}\n")
```

### JavaScript/Node.js Example

```javascript
const response = await fetch(
  "http://localhost:8000/api/v1/search?query=frontend%20developer%20in%20London"
);

const data = await response.json();
const jobs = data.data;

jobs.forEach(job => {
  console.log(`${job.job_title} at ${job.employer_name}`);
});
```

### WhatsApp Bot Example

```python
# In your WhatsApp bot
def search_jobs(user_query):
    response = requests.get(
        "http://your-server:8000/api/v1/search",
        params={"query": user_query}
    )
    
    jobs = response.json()['data'][:5]  # Top 5
    
    message = "🔥 *Top Jobs*\n\n"
    for i, job in enumerate(jobs, 1):
        message += f"{i}. {job['job_title']}\n"
        message += f"   🏢 {job['employer_name']}\n"
        message += f"   📍 {job['job_city']}\n"
        message += f"   👉 {job['job_apply_link']}\n\n"
    
    return message
```

---

## 📊 Response Format

```json
{
  "status": "OK",
  "request_id": "worqnow_abc123",
  "parameters": {
    "query": "developer in Lagos",
    "page": 1,
    "num_pages": 1
  },
  "data": [
    {
      "job_id": "worqnow_...",
      "job_title": "Software Developer",
      "employer_name": "Tech Company Ltd",
      "job_city": "Lagos",
      "job_state": "Lagos",
      "job_country": "Nigeria",
      "job_apply_link": "https://...",
      "job_description": "...",
      "job_is_remote": false,
      "job_posted_at_datetime_utc": "2026-03-12",
      "job_employment_type": "FULLTIME",
      "job_min_salary": 120000,
      "job_max_salary": 180000,
      "job_salary_currency": "NGN",
      "job_publisher": "LinkedIn"
    }
  ]
}
```

---

## 🔧 API Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ Yes | Natural language search (e.g., "developer in Lagos") |
| `page` | integer | No | Page number (default: 1) |
| `num_pages` | integer | No | Pages to fetch (default: 1, max: 10) |
| `date_posted` | string | No | Filter: `all`, `today`, `3days`, `week`, `month` |
| `remote_jobs_only` | boolean | No | Filter remote jobs only |
| `employment_types` | string | No | Filter: `FULLTIME`, `PARTTIME`, `CONTRACT`, `INTERN` |
| `format` | string | No | Response format: `json` or `csv` |

---

## 🌍 Global Coverage

Works in **195+ countries** with smart site selection:

- **Middle East** (UAE, Saudi, Qatar) → Uses Bayt + Indeed + LinkedIn
- **India** → Uses Naukri + Indeed + LinkedIn  
- **USA/Canada** → Uses Indeed + LinkedIn + ZipRecruiter + Glassdoor
- **UK** → Uses Indeed + LinkedIn + Glassdoor
- **All Others** → Uses Indeed + LinkedIn (works everywhere!)

**No country mapping needed** - just pass the location name and it works!

---

## 🐳 Production Deployment

### Option 1: Direct Python

```bash
# Install
pip install -r requirements.txt

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option 2: Docker

```bash
# Build
docker build -t worqnow-jobs-api .

# Run
docker run -p 8000:8000 worqnow-jobs-api
```

### Option 3: VPS (Recommended)

```bash
# On your VPS (DigitalOcean, Linode, AWS, etc.)
git clone https://github.com/ibrahimpelumi6142/worqnow-jobs-api.git
cd worqnow-jobs-api
pip install -r requirements.txt

# Run with screen or tmux
screen -S jobs-api
uvicorn main:app --host 0.0.0.0 --port 8000
# Ctrl+A, D to detach
```

---

## 🔐 Optional: API Key Authentication

For private deployments, enable API key protection:

```bash
# Create .env file
ENABLE_API_KEY_AUTH=true
API_KEYS=your-secret-key-1,your-secret-key-2
```

Then use:

```bash
curl "http://localhost:8000/api/v1/search?query=developer" \
  -H "x-api-key: your-secret-key-1"
```

---

## 🤝 Use Cases

Built for:

- 📱 **WhatsApp/Telegram Bots** - Job alerts and search
- 🌐 **Job Boards** - Power your aggregation platform
- 💼 **Career Platforms** - Add job search features
- 🤖 **Recruitment Tools** - Source candidates automatically
- 📊 **Market Research** - Analyze job trends by location/role
- 🚀 **Startup MVPs** - Quick job search integration

---

## 🏆 Used By

- **[WorqNow](https://worqnow.com)** - WhatsApp job assistant (200+ users across Nigeria, Kenya, Ghana)

*Using this in production? [Submit a PR](https://github.com/ibrahimpelumi6142/worqnow-jobs-api/pulls) to add your project!*

---

## 🛠 Built With

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[JobSpy](https://github.com/culclasure/jobspy)** - Job scraping engine (the real MVP!)
- **[Pandas](https://pandas.pydata.org/)** - Data processing

**Big thanks to [@culclasure](https://github.com/culclasure) for building JobSpy!** ⭐

---

## 📝 Requirements

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-jobspy==1.1.72
pandas==2.2.0
pydantic==2.6.0
```

---

## 🚨 Known Issues

- **Google Jobs removed** - JobSpy's Google scraper currently errors out, so we disabled it
- **Rate limits** - Job sites may rate-limit heavy usage (use reasonable intervals)
- **Dynamic content** - Some job details might be incomplete depending on source site

---

## 🤝 Contributing

Contributions welcome! 

1. Fork it
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📄 License

**MIT License** - see [LICENSE](LICENSE) file

**You can:**
- ✅ Use commercially
- ✅ Modify freely  
- ✅ Distribute
- ✅ Self-host privately or publicly

**You must:**
- 📄 Include original license and copyright

---

## 🙏 Credits

Built with ❤️ by [Ibrahim Pelumi Lasisi](https://github.com/ibrahimpelumi6142) for the [WorqNow](https://worqnow.ai) project.

**Powered by:**
- [JobSpy](https://github.com/culclasure/jobspy) by [@culclasure](https://github.com/culclasure)

---

## 🐛 Support

- 🐛 [Report bugs](https://github.com/ibrahimpelumi6142/worqnow-jobs-api/issues)
- 💡 [Request features](https://github.com/ibrahimpelumi6142/worqnow-jobs-api/issues)
- 💬 [Discussions](https://github.com/ibrahimpelumi6142/worqnow-jobs-api/discussions)

---

## 📧 Contact

- **Email:** hello@worqnow.com
- **Twitter:** [@worqnow](https://twitter.com/worqnow)
- **Website:** [worqnow.ai](https://worqnow.com)

---

## ⭐ Show Your Support

If this project saved you money or helped your project, please give it a ⭐️ on GitHub!

---

**Stop paying for job search APIs. Self-host this in 5 minutes.** 🚀
