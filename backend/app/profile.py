from pydantic import BaseModel, Field

from app.skills import extract_skills


class StudentProfile(BaseModel):
    summary: str = Field(
        description="One or two sentences on the student's background and what they want next. "
        "No names or contact details."
    )
    skills: list[str] = Field(description="Technical skills, tools and frameworks the student has actually used.")
    target_roles: list[str] = Field(
        description="2-4 realistic internship or entry-level role titles that fit the student, "
        "e.g. 'Machine Learning Intern'."
    )
    education: str | None = Field(default=None, description="Degree and field, e.g. 'B.Tech Computer Science'.")
    graduation_year: int | None = Field(default=None, description="Expected or actual graduation year.")
    years_experience: float = Field(
        default=0, description="Years of work experience; count internships by their real duration."
    )
    preferred_locations: list[str] = Field(default_factory=list, description="Cities the student mentions.")

    def matching_text(self) -> str:
        parts = [
            f"Looking for: {', '.join(self.target_roles)}.",
            f"Skills: {', '.join(self.skills)}.",
            self.summary,
        ]
        if self.education:
            parts.append(f"Education: {self.education}.")
        return " ".join(parts)

    def skill_set(self) -> set[str]:
        # Trailing comma lets case-sensitive aliases like "C" match at the end of the list.
        return extract_skills(", ".join(self.skills) + ",")

    def keyword_query(self) -> str:
        terms = [t.replace('"', "").strip() for t in self.target_roles + self.skills[:15]]
        return " or ".join(f'"{t}"' for t in terms if t)
