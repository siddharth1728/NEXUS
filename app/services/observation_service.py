import re

def generate_observations(artifact_type: str, file_path: str, content: str) -> list:
    observations = []
    
    if artifact_type == "dockerfile":
        observations.append({"text": "Dockerfile detected", "line_numbers": None})
    elif artifact_type == "github_action":
        observations.append({"text": "GitHub Actions workflow detected", "line_numbers": None})
    elif artifact_type == "python_test":
        observations.append({"text": "Test file detected", "line_numbers": None})
    
    # Text-based heuristics
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # FastAPI
        if re.search(r'from fastapi import|import fastapi', line):
            observations.append({"text": "FastAPI import detected", "line_numbers": str(line_num)})
        if re.search(r'@.*\.get\(|@.*\.post\(|@.*\.put\(|@.*\.delete\(', line) and 'router' in line.lower() or 'app' in line.lower():
            # A bit loose, but adequate for deterministic check
            if '@router.' in line or '@app.' in line:
                observations.append({"text": "API route definitions detected", "line_numbers": str(line_num)})
                
        # SQLAlchemy
        if re.search(r'from sqlalchemy import|import sqlalchemy', line):
            observations.append({"text": "SQLAlchemy dependency detected", "line_numbers": str(line_num)})
            
        # Pytest
        if re.search(r'pytest', line) and artifact_type in ["python_requirements", "python_project_config", "python_test"]:
            observations.append({"text": "Pytest dependency detected", "line_numbers": str(line_num)})
            
        # JWT
        if re.search(r'jwt\.encode|jwt\.decode', line) or 'jose' in line:
            observations.append({"text": "JWT authentication implementation detected", "line_numbers": str(line_num)})
            
        # Password hashing
        if re.search(r'bcrypt|passlib|hashpw|checkpw', line):
            observations.append({"text": "Password hashing implementation detected", "line_numbers": str(line_num)})
            
        # PostgreSQL
        if re.search(r'postgresql|psycopg', line):
            observations.append({"text": "PostgreSQL configuration detected", "line_numbers": str(line_num)})

    return observations
