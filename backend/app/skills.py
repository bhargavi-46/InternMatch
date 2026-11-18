"""A curated tech-skills vocabulary used to find matched and missing skills deterministically.

Each skill maps to regex aliases. Matching is case-insensitive unless the alias is listed in
CASE_SENSITIVE (single letters like "C" or "R" and words like "Go" that are common in plain English).
"""

import re

_SKILLS: dict[str, list[str]] = {
    # Languages
    "Python": [r"python"],
    "Java": [r"java(?!\s*script)"],
    "JavaScript": [r"javascript", r"\bjs\b"],
    "TypeScript": [r"typescript"],
    "C++": [r"c\+\+", r"\bcpp\b"],
    "C#": [r"c#", r"\.net\b", r"dotnet"],
    "Go": [r"golang"],
    "Rust": [r"\brust\b"],
    "Kotlin": [r"kotlin"],
    "Swift": [r"swiftui"],
    "Scala": [r"\bscala\b"],
    "Ruby": [r"\bruby\b", r"rails"],
    "PHP": [r"\bphp\b"],
    "SQL": [r"\bsql\b"],
    "Bash": [r"\bbash\b", r"shell scripting"],
    # Web and backend
    "React": [r"\breact(\.js|js)?\b"],
    "Next.js": [r"next\.?js"],
    "Angular": [r"angular"],
    "Vue": [r"\bvue(\.js)?\b"],
    "Node.js": [r"node\.?js"],
    "Express": [r"express\.?js"],
    "Django": [r"django"],
    "Flask": [r"\bflask\b"],
    "FastAPI": [r"fastapi"],
    "Spring": [r"spring ?boot", r"spring framework"],
    "HTML/CSS": [r"\bhtml5?\b", r"\bcss3?\b"],
    "Tailwind CSS": [r"tailwind"],
    "REST APIs": [r"\brest(ful)?\b(\s+apis?)?", r"\bapis?\b"],
    "GraphQL": [r"graphql"],
    "gRPC": [r"\bgrpc\b"],
    "WebSockets": [r"websockets?", r"socket\.io"],
    "Microservices": [r"micro-?services?"],
    # Data and storage
    "PostgreSQL": [r"postgres(ql)?"],
    "MySQL": [r"mysql"],
    "MongoDB": [r"mongo(db)?"],
    "Redis": [r"\bredis\b"],
    "Elasticsearch": [r"elastic\s?search"],
    "Kafka": [r"\bkafka\b"],
    "Spark": [r"\bspark\b", r"pyspark"],
    "Airflow": [r"airflow"],
    "Snowflake": [r"snowflake"],
    "dbt": [r"\bdbt\b"],
    "Pandas": [r"pandas"],
    "NumPy": [r"numpy"],
    "Data Analysis": [r"data analy(sis|tics)"],
    "Tableau": [r"tableau"],
    "Power BI": [r"power\s?bi"],
    "Excel": [r"\bexcel\b"],
    # ML and AI
    "Machine Learning": [r"machine learning", r"\bml\b"],
    "Deep Learning": [r"deep learning", r"neural networks?"],
    "PyTorch": [r"pytorch", r"\btorch\b"],
    "TensorFlow": [r"tensorflow", r"\bkeras\b"],
    "scikit-learn": [r"scikit-?learn", r"sklearn"],
    "NLP": [r"\bnlp\b", r"natural language processing"],
    "Computer Vision": [r"computer vision", r"\bopencv\b"],
    "LLMs": [r"\bllms?\b", r"large language models?", r"\bgpt\b", r"generative ai", r"\bgenai\b"],
    "RAG": [r"\brag\b", r"retrieval[- ]augmented"],
    "LangChain": [r"langchain"],
    "LangGraph": [r"langgraph"],
    "AI Agents": [r"\bai agents?\b", r"agentic", r"multi-agent"],
    "Prompt Engineering": [r"prompt engineering", r"\bprompting\b"],
    "Embeddings": [r"embeddings?"],
    "Vector Databases": [r"vector (databases?|db|stores?|search)", r"pgvector", r"pinecone", r"faiss", r"qdrant"],
    "Recommender Systems": [r"recommend(er|ation) (systems?|engines?)", r"\brecsys\b"],
    "Statistics": [r"statistic(s|al)"],
    "MLOps": [r"mlops", r"model deployment"],
    "OCR": [r"\bocr\b", r"tesseract"],
    # Cloud and DevOps
    "AWS": [r"\baws\b", r"amazon web services"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"google cloud"],
    "Docker": [r"docker", r"containeri[sz]"],
    "Kubernetes": [r"kubernetes", r"\bk8s\b"],
    "Terraform": [r"terraform"],
    "Ansible": [r"ansible"],
    "Puppet": [r"\bpuppet\b"],
    "CI/CD": [r"ci/cd", r"continuous (integration|delivery|deployment)", r"github actions", r"jenkins"],
    "Linux": [r"linux", r"\bunix\b"],
    "Git": [r"\bgit\b", r"github", r"gitlab"],
    "Networking": [r"computer networks?", r"tcp/ip", r"\bnetworking\b"],
    "Security": [r"cyber\s?security", r"information security", r"appsec", r"\bsecurity engineer"],
    # Fundamentals and practice
    "Data Structures & Algorithms": [r"data structures?", r"algorithms?", r"\bdsa\b"],
    "OOP": [r"\boop\b", r"object[- ]oriented"],
    "System Design": [r"system design", r"distributed systems?"],
    "DBMS": [r"\bdbms\b", r"database (design|management)"],
    "Operating Systems": [r"operating systems?"],
    "Testing": [r"unit test", r"\bpytest\b", r"\bjest\b", r"test automation", r"\bqa\b"],
    "Android": [r"android"],
    "iOS": [r"\bios\b"],
    "Flutter": [r"flutter"],
}

# Case-sensitive aliases for short names that are also everyday words or letters.
CASE_SENSITIVE: dict[str, list[str]] = {
    "Go": [r"\bGo\b(?=\s*(?:,|/|\)|and\b|or\b))"],
    "Swift": [r"\bSwift\b"],
    "Express": [r"\bExpress\b(?=\s*(?:,|/|\)|and\b|or\b))"],
    "C": [r"(?<![\w#+])C\b(?![+#])(?=\s*(?:,|/|\)|and\b|or\b))"],
    "R": [r"\bR\b(?=\s*(?:,|/|\)|and\b|or\b))"],
}

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (name, re.compile("|".join(f"(?:{a})" for a in aliases), re.IGNORECASE)) for name, aliases in _SKILLS.items()
] + [(name, re.compile("|".join(f"(?:{a})" for a in aliases))) for name, aliases in CASE_SENSITIVE.items()]

ALL_SKILLS = sorted({name for name, _ in _PATTERNS})


def extract_skills(text: str) -> set[str]:
    return {name for name, pattern in _PATTERNS if pattern.search(text)}
