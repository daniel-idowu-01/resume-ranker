# 🧠 AI Resume Ranker for Recruiters

An AI-powered backend platform that helps recruiters upload bulk resumes and rank them based on relevance to a given job description — using OpenAI embeddings and vector search (Pinecone). Built to demonstrate strong backend, AI, and system design skills for global engineering opportunities.

---

## 🚀 Demo

🌐 Live Demo: [resume-ranker.vercel.app](#)  
📬 API Docs: [Swagger UI](#)  
📦 Postman Collection: [Download](#)

---

## 🛠 Tech Stack

### Backend
- 🐍 FastAPI (Python)
- 🤖 OpenAI Embeddings (`text-embedding-ada-002`)
- 📦 Pinecone (Vector DB)
- 🧠 Resume Parser (`PyMuPDF`, `pdfminer`, `unstructured`)
- 🗂 MongoDB (Candidate data)
- 🔁 Celery + Redis (Async tasks)
- 🐳 Docker, GitHub Actions

### Frontend
- ⚛️ React (Vite)
- 💨 TailwindCSS
- 📡 Axios for API integration

---

## 📸 Features

- ✅ Upload multiple resumes (PDF)
- ✅ Submit job description text or file
- ✅ Parse resumes into structured data
- ✅ Match resumes to job using semantic search
- ✅ Rank results by AI relevance score
- ✅ View top candidates with metadata (name, email, score)
- ✅ Export results (CSV – planned)
- ✅ Deployed with CI/CD

---

## 📦 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload-resumes` | Upload one or more resumes (PDF) |
| `POST` | `/job-description` | Submit job description |
| `GET` | `/ranked-resumes` | Get ranked list of top candidates |

> Full API schema: [Postman Collection](#) | [Swagger](#)

---

## 🧱 System Architecture

![System Diagram](./docs/architecture.png)

---

## 🧠 How it Works

1. Recruiter uploads multiple resumes.
2. Resumes are parsed, cleaned, and stored.
3. Job description is embedded via OpenAI.
4. All resumes are embedded into Pinecone.
5. System performs vector search + cosine ranking.
6. Returns a sorted list of top candidates with relevance score.

## 📅 Project Roadmap

- ✅ Resume upload
- ✅ Resume parsing
- ✅ Job description input
- ✅ Embedding + matching
- ✅ Result ranking
- 📃 Export as CSV
- 📃 Admin dashboard
- 📃 Recruiter login system

---

## 🧪 Local Setup

```bash
# Clone the repo
git clone https://github.com/daniel-idowu-01/resume-ranker.git && cd resume-ranker

# Setup virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend
uvicorn app.main:app --reload

```
## 🤝 Contributing

PRs welcome. Please open an issue first to discuss major changes.

## 📜 License

MIT © Daniel @https://linkedin.com/in/daniel-idowu

