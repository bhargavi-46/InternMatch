"""Synthetic student personas used as eval queries.

A job counts as relevant to a persona when its title matches the persona's role pattern AND it is
open to students. Gain 2 = internship, 1 = entry-level, 0 = anything else. Labels come from rules,
not from the ranker being tested, so every method is judged against the same answer key.
"""

import re
from dataclasses import dataclass

from app.profile import StudentProfile


@dataclass
class Persona:
    name: str
    profile: StudentProfile
    role_pattern: re.Pattern[str]


def _persona(name: str, pattern: str, summary: str, skills: list[str], roles: list[str]) -> Persona:
    profile = StudentProfile(summary=summary, skills=skills, target_roles=roles, education="B.Tech Computer Science")
    return Persona(name, profile, re.compile(pattern, re.IGNORECASE))


PERSONAS: list[Persona] = [
    _persona(
        "ML / AI",
        r"machine learning|\bml\b|\bai\b|artificial intelligence|data scien|research",
        "Final-year student who trains deep learning models and builds LLM applications.",
        ["Python", "PyTorch", "scikit-learn", "LLMs", "RAG", "NLP", "SQL"],
        ["Machine Learning Intern", "AI Engineer Intern", "Data Science Intern"],
    ),
    _persona(
        "Backend",
        r"software|backend|back-end|\bsde\b|developer|full[- ]?stack|platform engineer",
        "Student who builds REST APIs and services with Python and Node.js.",
        ["Python", "Java", "Node.js", "FastAPI", "PostgreSQL", "Docker", "REST APIs", "Data Structures & Algorithms"],
        ["Software Engineer Intern", "Backend Developer Intern"],
    ),
    _persona(
        "Frontend",
        r"front[- ]?end|\bui\b|web developer|react",
        "Student who builds responsive web apps with React and TypeScript.",
        ["JavaScript", "TypeScript", "React", "Next.js", "HTML/CSS", "Tailwind CSS"],
        ["Frontend Developer Intern", "Web Developer Intern"],
    ),
    _persona(
        "Data analyst",
        r"data analy|business analy|analytics|\bbi\b|insights",
        "Student who analyses data with SQL and Python and builds dashboards.",
        ["SQL", "Python", "Pandas", "Excel", "Power BI", "Tableau", "Statistics"],
        ["Data Analyst Intern", "Business Analyst Intern"],
    ),
    _persona(
        "Security",
        r"security|infosec|\bsoc\b|appsec",
        "Student interested in application and cloud security, plays CTFs.",
        ["Python", "Linux", "Networking", "Security", "Bash", "AWS"],
        ["Security Engineer Intern", "Cybersecurity Intern"],
    ),
    _persona(
        "DevOps / Cloud",
        r"devops|cloud|\bsre\b|site reliability|infrastructure|platform",
        "Student who automates deployments and manages cloud infrastructure.",
        ["Linux", "Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Python", "Bash"],
        ["DevOps Intern", "Cloud Engineer Intern", "SRE Intern"],
    ),
    _persona(
        "Product",
        r"product|program|project",
        "Engineering student moving towards product management; ran college tech events.",
        ["SQL", "Data Analysis", "Excel"],
        ["Associate Product Manager Intern", "Product Intern", "Program Management Intern"],
    ),
    _persona(
        "Support engineering",
        r"support|customer|success|technical account",
        "Student who enjoys debugging customer problems and explaining technical topics.",
        ["Linux", "SQL", "Networking", "Python", "REST APIs"],
        ["Technical Support Engineer", "Customer Success Associate"],
    ),
]
