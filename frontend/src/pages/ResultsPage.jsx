import React from "react";
import ResultsComp from "../components/ResultsComp";

function ResultsPage() {
  const mockResults = {
    candidates: [
      {
        id: "1",
        name: "Jane Doe",
        email: "jane@example.com",
        phone: "08012345678",
        score: 92,
        experience: 5,
        location: "Lagos",
        skills: ["Python", "Django", "FastAPI", "MongoDB", "OpenAI"],
        summary:
          "Experienced backend developer with strong AI integration skills.",
        skillsMatch: 90,
        experienceMatch: 85,
        educationMatch: 88,
        notes: "Strong fit for AI-based backend projects.",
      },
      {
        id: "2",
        name: "John Smith",
        email: "john@example.com",
        phone: "08087654321",
        score: 78,
        experience: 3,
        location: "Abuja",
        skills: ["JavaScript", "Node.js", "Express", "React", "Redis"],
        summary: "Fullstack developer with solid experience in web apps.",
        skillsMatch: 72,
        experienceMatch: 65,
        educationMatch: 70,
        notes: "Good for frontend-backend integration roles.",
      },
      {
        id: "3",
        name: "Alice Johnson",
        email: "alice@example.com",
        phone: "07000001111",
        score: 61,
        experience: 2,
        location: "Ibadan",
        skills: ["PHP", "Laravel", "MySQL", "REST APIs"],
        summary: "Junior developer with backend potential.",
        skillsMatch: 60,
        experienceMatch: 58,
        educationMatch: 62,
        notes: "May need mentoring for AI-related tasks.",
      },
    ],
  };

  const mockJobDescription = `We are hiring a backend engineer to build AI-powered APIs for resume ranking. Must have experience with Python, FastAPI, MongoDB, and OpenAI tools.`;

  const handleNewSearch = () => {
    // Redirect or reset logic goes here
    alert("New search triggered.");
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <ResultsComp
        results={mockResults}
        jobDescription={mockJobDescription}
        onNewSearch={handleNewSearch}
      />
    </div>
  );
}

export default ResultsPage;
